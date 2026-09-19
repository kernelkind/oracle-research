#!/usr/bin/env node
// One caller-supplied prompt through pi-ai. No agent session, resources, tools, or retry loop.
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { zstdDecompressSync } from 'node:zlib';
import Ajv from 'ajv';
import Ajv2019 from 'ajv/dist/2019.js';
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { getSupportedThinkingLevels } from '@earendil-works/pi-ai';
import { OPENAI_CODEX_MODELS } from '@earendil-works/pi-ai/providers/openai-codex.models';
import { OPENROUTER_MODELS } from '@earendil-works/pi-ai/providers/openrouter.models';
import { stream as codexStream } from '@earendil-works/pi-ai/api/openai-codex-responses';
import { stream as openrouterStream } from '@earendil-works/pi-ai/api/openai-completions';

export const VERSION = 'oracle-model-runner/1';
const PI_AI_VERSION = '0.85.1';
const sha256 = text => createHash('sha256').update(text).digest('hex');
const nonempty = value => typeof value === 'string' && value.trim().length > 0;
const integer = (value, min, max) => Number.isSafeInteger(value) && value >= min && value <= max;

// This pinned catalog predates V4.1. Exact model metadata, not a V4 alias.
// OpenRouter /api/v1/models inspected 2026-09-16; catalog costs are not invoices or caps.
const deepseek = {
  id: 'deepseek/deepseek-v4.1-flash', name: 'DeepSeek V4.1 Flash',
  provider: 'openrouter', api: 'openai-completions', baseUrl: 'https://openrouter.ai/api/v1',
  input: ['text', 'image'], reasoning: true, contextWindow: 1048576, maxTokens: 384000,
  thinkingLevelMap: { off: 'none', low: 'low', high: 'high', max: 'max', minimal: null, medium: null, xhigh: null },
  cost: { input: 0.15, output: 0.60, cacheRead: 0.003, cacheWrite: 0 },
  compat: { supportsDeveloperRole: false, thinkingFormat: 'openrouter', maxTokensField: 'max_tokens' },
};

async function identity() {
  const hash = createHash('sha256');
  for (const path of ['model.mjs', 'package-lock.json', '../run-model.sh']) {
    const bytes = await readFile(new URL(path, import.meta.url));
    hash.update(`${path}\0${bytes.length}\0`).update(bytes);
  }
  return { runner_version: VERSION, pi_ai_version: PI_AI_VERSION, runner_sha256: hash.digest('hex') };
}

function compileSchema(schema) {
  if (typeof schema !== 'boolean' && (!schema || typeof schema !== 'object' || Array.isArray(schema))) {
    throw new Error('schema must be a JSON Schema object or boolean');
  }
  const dialect = schema.$schema;
  const Validator = dialect === 'https://json-schema.org/draft/2020-12/schema' ? Ajv2020
    : dialect === 'https://json-schema.org/draft/2019-09/schema' ? Ajv2019 : Ajv;
  // No coercion, defaults, property removal, remote schema loading, or unknown-keyword acceptance.
  const validator = new Validator({ strict: true, strictRequired: false, strictTypes: false, strictTuples: false, allowUnionTypes: true });
  addFormats(validator);
  try {
    const validate = validator.compile(schema);
    if (validate.$async) throw new Error('asynchronous schemas are unsupported');
    return validate;
  }
  catch (error) { throw new Error(`Invalid or unsupported JSON schema: ${error.message}`); }
}

/** Prepare the exact prompt and explicitly selected route, without reading any task inputs. */
export async function prepare(config) {
  if (!config || typeof config !== 'object' || Array.isArray(config)) throw new Error('Config must be an object');
  const allowed = new Set(['provider', 'model', 'reasoning', 'prompt', 'schema', 'max_output_tokens', 'timeout_seconds']);
  for (const key of Object.keys(config)) if (!allowed.has(key)) throw new Error(`Unknown config field: ${key}`);
  if (typeof config.prompt !== 'string') throw new Error('prompt must be a string');
  if (!nonempty(config.model)) throw new Error('model must be a nonempty string');
  // pi-ai removes unpaired surrogates. Refuse them instead of silently changing the prompt.
  if (!config.prompt.isWellFormed()) throw new Error('prompt must contain well-formed Unicode; unpaired surrogates are unsupported');
  let model;
  if (config.provider === 'openai-codex') {
    model = Object.hasOwn(OPENAI_CODEX_MODELS, config.model) ? OPENAI_CODEX_MODELS[config.model] : undefined;
    if (!model) throw new Error('Unknown subscription model in the pinned pi-ai catalog; no model substitution');
    if (model.api !== 'openai-codex-responses') throw new Error(`Unsupported subscription transport: ${model.api}`);
    if ('max_output_tokens' in config) throw new Error('pi-ai subscription transport does not enforce an output token cap; use timeout_seconds');
  } else if (config.provider === 'openrouter') {
    model = config.model === deepseek.id ? deepseek : Object.hasOwn(OPENROUTER_MODELS, config.model) ? OPENROUTER_MODELS[config.model] : undefined;
    if (!model) throw new Error('Unknown OpenRouter model in the pinned pi-ai catalog; no model substitution');
    if (model.api !== 'openai-completions') throw new Error(`Unsupported OpenRouter transport: ${model.api}; this runner supports openai-completions, without rerouting models`);
    if (!integer(config.max_output_tokens, 1, model.maxTokens)) throw new Error('OpenRouter requires max_output_tokens within the model limit');
    model = { ...model, compat: { ...model.compat, maxTokensField: 'max_tokens' } };
  } else {
    throw new Error('provider must be openai-codex (subscription) or openrouter');
  }
  if (config.reasoning !== 'provider-default' && !getSupportedThinkingLevels(model).includes(config.reasoning)) {
    throw new Error('Unsupported reasoning setting; choose a supported effort or provider-default');
  }
  const timeout = config.timeout_seconds ?? 300;
  if (!integer(timeout, 1, 3600)) throw new Error('timeout_seconds must be an integer from 1 to 3600');
  const hasSchema = Object.hasOwn(config, 'schema');
  const schema = hasSchema ? structuredClone(config.schema) : null;
  const validate = hasSchema ? compileSchema(schema) : null;
  return {
    model, reasoning: config.reasoning, prompt: config.prompt,
    max_output_tokens: config.max_output_tokens ?? null, timeout_seconds: timeout,
    prompt_sha256: sha256(config.prompt), schema, schema_name: 'output',
    schema_sha256: hasSchema ? sha256(JSON.stringify(schema)) : null, validate,
  };
}

function formatPayload(payload, request) {
  if (request.model.provider === 'openai-codex') {
    // The serializer otherwise injects a system instruction and output preferences.
    payload.instructions = '';
    delete payload.tool_choice;
    delete payload.parallel_tool_calls;
    delete payload.include;
    if (payload.reasoning) delete payload.reasoning.summary;
    if (request.schema !== null) payload.text = {
      format: { type: 'json_schema', name: request.schema_name, strict: true, schema: request.schema },
    };
    else delete payload.text;
  } else {
    if (request.reasoning === 'provider-default') delete payload.reasoning;
    if (request.schema !== null) payload.response_format = {
      type: 'json_schema', json_schema: { name: request.schema_name, strict: true, schema: request.schema },
    };
    payload.provider = { require_parameters: true, allow_fallbacks: false };
  }
  return payload;
}

function safeHeaders(headers) {
  return Object.fromEntries([...new Headers(headers)].map(([key, value]) =>
    [key, /authorization|api-key|cookie|account-id/i.test(key) ? '[REDACTED]' : value]));
}

async function wireRequest(input, options) {
  const request = new Request(input, options);
  let body = Buffer.from(await request.arrayBuffer());
  if (request.headers.get('content-encoding') === 'zstd') body = zstdDecompressSync(body);
  return { url: request.url, method: request.method, headers: safeHeaders(request.headers), body: JSON.parse(body.toString('utf8')) };
}

// Observe bounded per-event metadata, not a second copy of the complete token stream.
function observeResponse(response, metadata) {
  metadata.http_status = response.status;
  const requestId = response.headers.get('x-request-id');
  if (requestId) metadata.request_id = requestId;
  if (!response.ok || !response.body || !response.headers.get('content-type')?.includes('text/event-stream')) return response;
  const decoder = new TextDecoder();
  let buffer = '';
  let data = [];
  function dispatch() {
    if (!data.length) return;
    try {
      const event = JSON.parse(data.join('\n'));
      const value = event.response ?? event;
      for (const key of ['id', 'model', 'provider', 'usage', 'service_tier']) {
        if (value[key] !== undefined && value[key] !== null) metadata[key] = value[key];
      }
    } catch { /* [DONE] or non-JSON event; pi-ai remains the response parser. */ }
    data = [];
  }
  function line(value) {
    if (!value) dispatch();
    else if (value.startsWith('data:')) data.push(value.slice(5).replace(/^ /, ''));
  }
  function consume() {
    let end;
    while ((end = buffer.indexOf('\n')) >= 0) {
      line(buffer.slice(0, end).replace(/\r$/, ''));
      buffer = buffer.slice(end + 1);
    }
  }
  const body = response.body.pipeThrough(new TransformStream({
    transform(chunk, controller) {
      buffer += decoder.decode(chunk, { stream: true });
      consume();
      controller.enqueue(chunk);
    },
    flush() {
      buffer += decoder.decode();
      consume();
      if (buffer) line(buffer.replace(/\r$/, ''));
      dispatch();
    },
  }));
  return new Response(body, { status: response.status, statusText: response.statusText, headers: response.headers });
}

function checkOutput(request, raw, stopReason) {
  if (stopReason !== 'stop') return { valid: false, output: null, validation_error: `Generation ended with ${stopReason}` };
  if (request.schema === null) return { valid: true, output: raw, validation_error: null };
  let output;
  try { output = JSON.parse(raw); }
  catch { return { valid: false, output: null, validation_error: 'Output is not bare JSON' }; }
  const valid = request.validate(output);
  return { valid, output, validation_error: valid ? null : `Output does not match JSON schema: ${JSON.stringify(request.validate.errors)}` };
}

function redactor(apiKey) {
  const secrets = [apiKey];
  try {
    const account = JSON.parse(Buffer.from(apiKey.split('.')[1], 'base64url').toString('utf8'))['https://api.openai.com/auth']?.chatgpt_account_id;
    if (nonempty(account)) secrets.push(account);
  } catch { /* API keys need no JWT decoding. */ }
  function redact(value) {
    if (typeof value === 'string') return secrets.reduce((text, secret) => text.replaceAll(secret, '[REDACTED]'), value);
    if (Array.isArray(value)) return value.map(redact);
    if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, redact(item)]));
    return value;
  }
  return redact;
}

/** Invoke pi-ai once through an explicit credential and transport. No auth discovery or fallback. */
export async function execute(request, { apiKey, fetch = globalThis.fetch, signal } = {}) {
  if (!nonempty(apiKey)) throw new Error('Explicit credentials are required for execution');
  const provenance = await identity();
  const redact = redactor(apiKey);
  const abort = AbortSignal.any([AbortSignal.timeout(request.timeout_seconds * 1000), ...(signal ? [signal] : [])]);
  let wire;
  let calls = 0;
  const responseMetadata = {};
  const options = {
    apiKey, transport: 'sse', cacheRetention: 'none', maxRetries: 0, timeoutMs: request.timeout_seconds * 1000,
    signal: abort,
    reasoningEffort: request.reasoning === 'provider-default' ? undefined : request.reasoning === 'off' ? 'none' : request.reasoning,
    ...(request.max_output_tokens === null ? {} : { maxTokens: request.max_output_tokens }),
    onPayload: payload => formatPayload(payload, request),
    fetch: async (input, init) => {
      if (calls !== 0) throw new Error('Only one HTTP attempt is permitted');
      calls++;
      wire = await wireRequest(input, init);
      return observeResponse(await fetch(input, init), responseMetadata);
    },
  };
  const context = { messages: [{ role: 'user', content: request.prompt, timestamp: 0 }] };
  const stream = request.model.provider === 'openai-codex' ? codexStream : openrouterStream;
  const started = Date.now();
  const events = stream(request.model, context, options);
  for await (const _event of events) { /* Drain incrementally; the final message retains the output. */ }
  const result = await events.result();
  const raw = result.content.filter(item => item.type === 'text').map(item => item.text).join('');
  return {
    ...provenance, provider: request.model.provider, model: request.model.id, reasoning: request.reasoning,
    prompt_sha256: request.prompt_sha256, schema_sha256: request.schema_sha256,
    elapsed_ms: Date.now() - started, request: wire ?? null, response_metadata: redact(responseMetadata),
    response_id: redact(result.responseId ?? null), response_model: redact(result.responseModel ?? null),
    provider_thinking_level: result.providerThinkingLevel ?? null,
    http_attempts: calls, stop_reason: result.stopReason, raw_stop_reason: result.rawStopReason ?? null,
    diagnostics: redact(result.diagnostics ?? []), error: redact(result.errorMessage ?? null),
    raw_text: raw, usage: result.usage,
    usage_note: 'pi-ai input excludes cacheRead/cacheWrite; output includes reasoning. SDK cost is a catalog estimate, not an invoice or subscription charge.',
    ...checkOutput(request, raw, result.stopReason),
  };
}

/** Use actual SDK serializers with fabricated credentials and a transport that cannot send. */
export async function preview(request) {
  const fakeToken = 'preview.' + Buffer.from(JSON.stringify({
    'https://api.openai.com/auth': { chatgpt_account_id: 'offline-preview' },
  })).toString('base64') + '.not-a-signature';
  const result = await execute(request, {
    apiKey: request.model.provider === 'openai-codex' ? fakeToken : 'offline-preview',
    fetch: async () => new Response('{"error":{"message":"Offline preview: no request sent"}}', { status: 400 }),
  });
  if (!result.request || result.http_attempts !== 1) throw new Error('pi-ai could not serialize this request for preview');
  return {
    runner_version: result.runner_version, pi_ai_version: result.pi_ai_version, runner_sha256: result.runner_sha256,
    provider: result.provider, model: result.model, reasoning: result.reasoning,
    prompt_sha256: request.prompt_sha256, schema_sha256: request.schema_sha256, prompt: request.prompt,
    credentials_read: false, network_requests: 0, ...result.request,
    notice: 'Actual pi-ai HTTP body decoded for inspection; authentication headers are placeholders. Server acceptance and hidden provider behavior are untested.',
  };
}

export async function subscriptionToken(path) {
  if (!path) throw new Error('Subscription execution requires --auth-file (explicit Codex or pi OAuth file)');
  let auth;
  try { auth = JSON.parse(await readFile(path, 'utf8')); }
  catch { throw new Error('Cannot read the specified authentication file'); }
  const credential = auth['openai-codex'];
  const token = auth.tokens?.access_token ?? (credential?.type === 'oauth' ? credential.access : undefined);
  try {
    if (!token || token.split('.').length !== 3) throw new Error();
    const claims = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString('utf8'));
    if (!claims['https://api.openai.com/auth']?.chatgpt_account_id ||
        !Number.isFinite(claims.exp) || claims.exp * 1000 <= Date.now() + 30000) throw new Error();
  } catch { throw new Error('A valid, unexpired subscription OAuth token is required; no API-key fallback or automatic refresh'); }
  return token;
}

async function localPiConnection() {
  // agent-account owns selection. Read only the native Pi files in this
  // process's selected view; never reselect via a child Pi invocation.
  try {
    const directory = process.env.PI_CODING_AGENT_DIR || join(homedir(), '.pi', 'agent');
    const models = JSON.parse(await readFile(join(directory, 'models.json'), 'utf8'));
    const auth = JSON.parse(await readFile(join(directory, 'auth.json'), 'utf8'));
    const provider = models.providers?.['openai-codex'];
    const credential = auth['openai-codex'];
    const endpoint = new URL(provider.baseUrl);
    if (endpoint.protocol !== 'http:' || !['127.0.0.1', '[::1]'].includes(endpoint.hostname) ||
        !endpoint.port || endpoint.username || endpoint.password || endpoint.search || endpoint.hash ||
        !/^\/[A-Za-z0-9_-]+\/pi\/?$/.test(endpoint.pathname) ||
        credential?.type !== 'api_key' || !nonempty(credential.key) ||
        credential.key !== provider.apiKey) throw new Error();
    return { baseUrl: endpoint.href.replace(/\/$/, ''), apiKey: credential.key };
  } catch {
    // Do not export a real bearer or fall back to the upstream endpoint.
    throw new Error('Valid local Pi configuration is required; run through agent-account exec pi');
  }
}

const help = `Usage: run-model.sh preview|run [CONFIG.json] [--send] [--auth-file PATH | --pi-config]
Reads one JSON config from file or stdin; writes one JSON result to stdout.
Required: provider, model, reasoning, prompt (sent exactly as supplied).
Optional: schema, timeout_seconds (default 300). No tools, history, retries, or prompt repair.
Providers: openai-codex subscription; OpenRouter models using pi-ai openai-completions.
Other catalog transports are rejected explicitly; no model substitution or rerouting.
OpenRouter requires max_output_tokens. Subscription output caps are unsupported.
reasoning selects a supported pi-ai effort or provider-default (no requested preference).
schema is validated locally without coercion; omitted schema accepts plain text.
JSON Schema draft-07 (default), 2019-09, and 2020-12 are supported without remote refs.
Provider schema support may be narrower; unsupported parameters remain request failures.
preview cannot send and reads no credentials. run requires --send.
Subscription auth: explicit --auth-file; no refresh or paid OpenAI API fallback.
--pi-config: use the local credential-service endpoint and access token from native Pi configuration.
Launch this mode through agent-account exec pi; no upstream credential export or fallback.
OpenRouter auth: OPENROUTER_API_KEY. Never reads OPENAI_API_KEY.
--version prints versions; --identity prints versions and source/dependency SHA-256.
Before paid execution, obtain approved maximum spend, record the commitment in
budget-ledger.json, and configure the required external provider-side spending limit.
Timeouts/output limits are not spending approval or monetary hard caps.
`;

async function main() {
  const { values, positionals } = parseArgs({ allowPositionals: true, options: {
    help: { type: 'boolean' }, version: { type: 'boolean' }, identity: { type: 'boolean' },
    send: { type: 'boolean' }, 'auth-file': { type: 'string' }, 'pi-config': { type: 'boolean' },
  } });
  if (values.help) { process.stdout.write(help); return; }
  if (values.version) { process.stdout.write(`${VERSION} pi-ai/${PI_AI_VERSION}\n`); return; }
  if (values.identity) { process.stdout.write(JSON.stringify(await identity()) + '\n'); return; }
  const [command, path] = positionals;
  if (!['preview', 'run'].includes(command) || positionals.length > 2) throw new Error(help);
  if (command === 'run' && !values.send) throw new Error('Sending requires the explicit --send flag');
  if (values['pi-config'] && values['auth-file']) throw new Error('--pi-config and --auth-file cannot be combined');
  if (command === 'preview' && (values.send || values['auth-file'])) throw new Error('preview does not accept --send or --auth-file');
  const input = path ? await readFile(path, 'utf8') : await new Response(process.stdin).text();
  const request = await prepare(JSON.parse(input));
  if (values['pi-config'] && request.model.provider !== 'openai-codex') throw new Error('--pi-config is for openai-codex only');
  if (command === 'preview') { process.stdout.write(JSON.stringify(await preview(request), null, 2) + '\n'); return; }
  if (request.model.provider === 'openrouter' && values['auth-file']) throw new Error('OpenRouter uses OPENROUTER_API_KEY, not --auth-file');
  let apiKey;
  if (values['pi-config']) {
    const connection = await localPiConnection();
    request.model = { ...request.model, baseUrl: connection.baseUrl };
    apiKey = connection.apiKey;
  } else {
    apiKey = request.model.provider === 'openai-codex'
      ? await subscriptionToken(values['auth-file']) : process.env.OPENROUTER_API_KEY;
  }
  const result = await execute(request, { apiKey });
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
  if (!result.valid) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(error => { process.stderr.write(`${error.message}\n`); process.exitCode = 1; });
}
