#!/usr/bin/env node
// A single independent extraction call. No coding-agent session, resources, or tool loop.
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';
import { zstdDecompressSync } from 'node:zlib';
import { OPENAI_CODEX_MODELS } from '@earendil-works/pi-ai/providers/openai-codex.models';
import { OPENROUTER_MODELS } from '@earendil-works/pi-ai/providers/openrouter.models';
import { stream as codexStream } from '@earendil-works/pi-ai/api/openai-codex-responses';
import { stream as openrouterStream } from '@earendil-works/pi-ai/api/openai-completions';

const root = new URL('../', import.meta.url);
const sha256 = text => createHash('sha256').update(text).digest('hex');
const read = path => readFile(new URL(path, root), 'utf8');
const NIP19 = /(?<![A-Za-z0-9_])(?:nostr:)?(?:nprofile|nevent|nrelay|naddr|npub|nsec|note)1[023456789acdefghjklmnpqrstuvwxyz]{20,}(?:[?#][^\s<>"']*)?(?=$|[^A-Za-z0-9_])/gi;

// This release's catalog predates V4.1. Explicit metadata, not a V4 model alias.
// https://openrouter.ai/api/v1/models, inspected 2026-09-16.
// canonical_slug: deepseek/deepseek-v4.1-flash-20260910. Prices are NOT an invoice or spend cap.
const deepseek = {
  id: 'deepseek/deepseek-v4.1-flash', name: 'DeepSeek V4.1 Flash',
  provider: 'openrouter', api: 'openai-completions', baseUrl: 'https://openrouter.ai/api/v1',
  input: ['text', 'image'], reasoning: true, contextWindow: 1048576, maxTokens: 384000,
  thinkingLevelMap: { off: 'none', low: 'low', high: 'high', max: 'max' },
  cost: { input: 0.15, output: 0.60, cacheRead: 0.003, cacheWrite: 0 },
  compat: { supportsDeveloperRole: false, thinkingFormat: 'openrouter', maxTokensField: 'max_tokens' },
};

async function frozen(path, expected) {
  const text = await read(path);
  if (sha256(text) !== expected) throw new Error(`Frozen input changed: ${path}`);
  return text;
}

async function prompts() {
  const [subject, mask, schema] = await Promise.all([
    frozen('subject-prompt-goal-v1/asv6.23/ASv6.23.md', 'b80fd158b27ee0b3ddd640f10e78d7a18101f933d8758af749f6f3d2f25d506f'),
    frozen('mask-prompt-goal-v1/subject-deletion-v1/mask-prompt.md', '3bfaae265284e7b27fc0b740c7c4b214db8045d9f316f59990d5b36332d6c3e2'),
    frozen('subject-prompt-goal-v1/asv6.23/output-schema.json', 'f4fe9090fa4843397605c1a7bc163245f1cc15b71fefcef89ed31357e85f1070'),
  ]);
  return { subject, mask, schema: JSON.parse(schema) };
}

function nonempty(value) { return typeof value === 'string' && value.trim().length > 0; }
function integer(value, min, max) { return Number.isSafeInteger(value) && value >= min && value <= max; }

/** Prepare one independent request; coverage annotations and auxiliary subject context never enter it. */
export async function prepare(config) {
  const allowed = new Set(['provider', 'model', 'reasoning', 'stage', 'text', 'note_id', 'subject', 'max_output_tokens', 'timeout_seconds']);
  if (!config || typeof config !== 'object' || Array.isArray(config)) throw new Error('Config must be an object');
  for (const key of Object.keys(config)) if (!allowed.has(key)) throw new Error(`Unknown config field: ${key}`);
  if (!['subjects', 'masks'].includes(config.stage)) throw new Error('stage must be subjects or masks');
  if (('text' in config) === ('note_id' in config)) throw new Error('Supply exactly one of text or note_id');
  if (config.stage === 'masks' && !nonempty(config.subject)) throw new Error('masks requires one fixed subject string');
  if (config.stage === 'subjects' && 'subject' in config) throw new Error('subjects does not take a subject');
  let source;
  if ('note_id' in config) {
    const selection = JSON.parse(await read('frontier-model-comparison-v1/english-selection-v2/selection.json'));
    const matches = selection.notes.filter(n => n.id === config.note_id || n.note_id === config.note_id);
    if (matches.length !== 1) throw new Error('note_id must identify exactly one frozen selected note');
    const note = matches[0];
    source = { id: note.id, note_id: note.note_id, text: note.text };
  } else {
    source = { id: null, note_id: null, text: config.text };
  }
  if (!nonempty(source.text)) throw new Error('text must be a nonempty string');
  let model;
  if (config.provider === 'openai-codex') {
    if (config.model !== 'gpt-6-astra' || config.reasoning !== 'low') throw new Error('The frozen Astra baseline requires gpt-6-astra, low');
    model = OPENAI_CODEX_MODELS[config.model];
    if ('max_output_tokens' in config) throw new Error('pi-ai subscription transport does not enforce an output token cap; use timeout_seconds');
  } else if (config.provider === 'openrouter') {
    model = config.model === deepseek.id ? deepseek : OPENROUTER_MODELS[config.model];
    if (!model || model.api !== 'openai-completions') throw new Error('Unknown or unsupported OpenRouter model; no model substitution');
    if (!integer(config.max_output_tokens, 1, model.maxTokens)) throw new Error('OpenRouter requires max_output_tokens within the model limit');
    // OpenRouter's native field; do not rely on an OpenAI-specific compatibility default.
    model = { ...model, compat: { ...model.compat, maxTokensField: 'max_tokens' } };
  } else {
    throw new Error('provider must be openai-codex (subscription) or openrouter');
  }
  if (config.reasoning !== 'provider-default') {
    if (!nonempty(config.reasoning) || !model.thinkingLevelMap ||
        !Object.hasOwn(model.thinkingLevelMap, config.reasoning) || model.thinkingLevelMap[config.reasoning] === null) {
      throw new Error('Unsupported reasoning setting; choose an explicitly supported effort or provider-default');
    }
  }
  const timeout = config.timeout_seconds ?? 300;
  if (!integer(timeout, 1, 3600)) throw new Error('timeout_seconds must be an integer from 1 to 3600');
  const p = await prompts();
  const normalized = source.text.replace(NIP19, '');
  const prompt = config.stage === 'subjects'
    ? `${p.subject}\n\n<post>\n${normalized}\n</post>`
    : p.mask.replace(/\{POST\}|\{SUBJECT\}/g, key => key === '{POST}' ? source.text : config.subject);
  return {
    model, stage: config.stage, reasoning: config.reasoning,
    max_output_tokens: config.max_output_tokens ?? null, timeout_seconds: timeout,
    source, subject: config.subject ?? null, prompt,
    prompt_version: config.stage === 'subjects' ? 'ASv6.23' : 'MPv3.5',
    prompt_sha256: sha256(prompt), source_sha256: sha256(source.text),
    schema: config.stage === 'subjects' ? p.schema : null,
    schema_sha256: config.stage === 'subjects' ? sha256(JSON.stringify(p.schema)) : null,
    normalization_changed: config.stage === 'subjects' && normalized !== source.text,
  };
}

function formatPayload(payload, request) {
  if (request.model.provider === 'openai-codex') {
    // pi-ai otherwise injects "You are a helpful assistant." even with no systemPrompt.
    payload.instructions = '';
    delete payload.tool_choice;
    delete payload.parallel_tool_calls;
    delete payload.include; // No encrypted history is reused between independent calls.
    if (request.schema) payload.text.format = { type: 'json_schema', name: 'subjects', strict: true, schema: request.schema };
  } else {
    if (request.reasoning === 'provider-default') delete payload.reasoning;
    if (request.schema) payload.response_format = {
      type: 'json_schema', json_schema: { name: 'subjects', strict: true, schema: request.schema },
    };
    // Fail rather than silently routing to an endpoint which ignores our requested parameters.
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

// Preserve provider/model/usage metadata which a unified SDK may not expose. Do not buffer all streamed tokens.
function observeResponse(response, metadata) {
  if (!response.ok || !response.body || !response.headers.get('content-type')?.includes('text/event-stream')) return response;
  const decoder = new TextDecoder();
  let buffer = '';
  const body = response.body.pipeThrough(new TransformStream({
    transform(chunk, controller) {
      buffer += decoder.decode(chunk, { stream: true });
      let end;
      while ((end = buffer.indexOf('\n')) >= 0) {
        const line = buffer.slice(0, end).trimEnd();
        buffer = buffer.slice(end + 1);
        if (!line.startsWith('data:')) continue;
        try {
          const event = JSON.parse(line.slice(5));
          const data = event.response ?? event;
          for (const key of ['id', 'model', 'provider', 'usage', 'service_tier']) {
            if (data[key] !== undefined) metadata[key] = data[key];
          }
        } catch { /* [DONE], or a non-JSON event; pi-ai remains the response parser. */ }
      }
      controller.enqueue(chunk);
    },
  }));
  return new Response(body, { status: response.status, statusText: response.statusText, headers: response.headers });
}

function checkOutput(request, raw, stopReason) {
  if (stopReason !== 'stop') return { valid: false, output: null, validation_error: `Generation ended with ${stopReason}` };
  let output;
  try { output = JSON.parse(raw); }
  catch { return { valid: false, output: null, validation_error: 'Output is not bare JSON' }; }
  if (request.stage === 'subjects') {
    const valid = output && !Array.isArray(output) && Object.keys(output).length === 1 &&
      Array.isArray(output.subjects) && output.subjects.every(s => s && !Array.isArray(s) &&
        Object.keys(s).length === 2 && nonempty(s.context) && nonempty(s.subject));
    return { valid: !!valid, output, validation_error: valid ? null : 'Output does not match the frozen subject schema' };
  }
  if (!Array.isArray(output) || output.length === 0 || !output.every(nonempty)) {
    return { valid: false, output, validation_error: 'Mask must be a nonempty array of nonempty strings' };
  }
  let end = 0;
  for (const fragment of output) {
    const start = request.source.text.indexOf(fragment, end);
    if (start === -1) return { valid: false, output, validation_error: 'Mask fragments are not exact source substrings in source order' };
    end = start + fragment.length;
  }
  return { valid: true, output, validation_error: null };
}

/** Invoke pi-ai once. fetch is the actual transport, also used by the offline preview. No repair/retry loop. */
export async function execute(request, { apiKey, fetch = globalThis.fetch, signal } = {}) {
  if (!nonempty(apiKey)) throw new Error('Explicit credentials are required for execution');
  const abort = AbortSignal.any([AbortSignal.timeout(request.timeout_seconds * 1000), ...(signal ? [signal] : [])]);
  let wire;
  let calls = 0;
  const responseMetadata = {};
  const options = {
    apiKey, transport: 'sse', maxRetries: 0, timeoutMs: request.timeout_seconds * 1000,
    signal: abort,
    reasoningEffort: request.reasoning === 'provider-default' ? undefined : request.reasoning,
    ...(request.max_output_tokens === null ? {} : { maxTokens: request.max_output_tokens }),
    onPayload: payload => formatPayload(payload, request),
    fetch: async (input, init) => {
      if (++calls > 1) throw new Error('Only one HTTP attempt is permitted');
      wire = await wireRequest(input, init);
      const response = await fetch(input, init);
      return observeResponse(response, responseMetadata);
    },
  };
  // Each invocation starts from this new one-message context. No model tools or system prompt.
  const context = { messages: [{ role: 'user', content: request.prompt, timestamp: 0 }] };
  const stream = request.model.provider === 'openai-codex' ? codexStream : openrouterStream;
  const started = Date.now();
  const events = stream(request.model, context, options);
  // Drain events as they arrive instead of retaining an unread queue for the full generation.
  for await (const _event of events) { /* The final message below contains the generated output. */ }
  const result = await events.result();
  const raw = result.content.filter(x => x.type === 'text').map(x => x.text).join('');
  return {
    pi_ai_version: '0.85.1', provider: request.model.provider, model: request.model.id,
    stage: request.stage, source_id: request.source.id, note_id: request.source.note_id,
    source_sha256: request.source_sha256, prompt_version: request.prompt_version,
    prompt_sha256: request.prompt_sha256, schema_sha256: request.schema_sha256,
    elapsed_ms: Date.now() - started, request: wire ?? null, response_metadata: responseMetadata,
    http_attempts: calls, stop_reason: result.stopReason,
    error: result.errorMessage?.replaceAll(apiKey, '[REDACTED]') ?? null,
    raw_text: raw, usage: result.usage,
    usage_note: 'pi-ai input excludes cacheRead/cacheWrite; output includes reasoning. SDK cost is a catalog estimate, not an invoice or subscription charge.',
    ...checkOutput(request, raw, result.stopReason),
  };
}

/** Run the real serializers with fabricated credentials and a transport that cannot send. */
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
    pi_ai_version: result.pi_ai_version, provider: result.provider, model: result.model,
    stage: request.stage, source_id: request.source.id, note_id: request.source.note_id,
    prompt_version: request.prompt_version, prompt_sha256: request.prompt_sha256,
    source_sha256: request.source_sha256, schema_sha256: request.schema_sha256,
    normalization_changed: request.normalization_changed, prompt: request.prompt,
    credentials_read: false, network_requests: 0, ...result.request,
    notice: 'Actual pi-ai HTTP body decoded for inspection; authentication headers are placeholders. Server acceptance and hidden provider behavior are untested.',
  };
}

async function subscriptionToken(path) {
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

const help = `Usage: run-frontier-comparison.sh preview|run [CONFIG.json] [--send] [--auth-file PATH]
Reads a single config from the file or stdin; writes a single JSON result to stdout.
Required: provider, model, reasoning, stage; exactly one of note_id or text.
Stages: subjects (ASv6.23); masks (MPv3.5, also requires one fixed subject string).
Providers: openai-codex (gpt-6-astra, low), openrouter (exact pi-ai model ID).
OpenRouter also requires max_output_tokens; reasoning can be provider-default.
Optional: timeout_seconds (default 300). No retries, implicit batches, or prompt repair.
preview reads no credentials and cannot send requests. It uses the real pi-ai serializers.
run requires --send. Subscription auth: explicit --auth-file, no automatic refresh.
OpenRouter auth: OPENROUTER_API_KEY. Never uses OPENAI_API_KEY or the OpenAI paid API.
Before paid execution, obtain approved maximum spend, record the commitment in
budget-ledger.json, and configure the required external provider-side spending limit.
Timeouts/output limits are not spending approval or a monetary hard cap.
Local output checks test JSON/source integrity, NOT semantic correctness.
`;

async function main() {
  const { values, positionals } = parseArgs({ allowPositionals: true, options: {
    help: { type: 'boolean' }, send: { type: 'boolean' }, 'auth-file': { type: 'string' },
  } });
  if (values.help) { process.stdout.write(help); return; }
  const [command, path] = positionals;
  if (!['preview', 'run'].includes(command) || positionals.length > 2) throw new Error(help);
  if (command === 'run' && !values.send) throw new Error('Sending requires the explicit --send flag');
  if (command === 'preview' && (values.send || values['auth-file'])) throw new Error('preview does not accept --send or --auth-file');
  const input = path ? await readFile(path, 'utf8') : await new Response(process.stdin).text();
  const request = await prepare(JSON.parse(input));
  if (command === 'preview') { process.stdout.write(JSON.stringify(await preview(request), null, 2) + '\n'); return; }
  const apiKey = request.model.provider === 'openai-codex'
    ? await subscriptionToken(values['auth-file']) : process.env.OPENROUTER_API_KEY;
  if (request.model.provider === 'openrouter' && values['auth-file']) throw new Error('OpenRouter uses OPENROUTER_API_KEY, not --auth-file');
  const result = await execute(request, { apiKey });
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
  if (!result.valid) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(error => { process.stderr.write(`${error.message}\n`); process.exitCode = 1; });
}
