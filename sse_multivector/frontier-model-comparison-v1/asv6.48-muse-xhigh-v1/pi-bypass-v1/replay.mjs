// Diagnostic HTTP replay. No Pi or OpenAI SDK imports.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const hash = value => createHash('sha256').update(value).digest('hex');

export async function replay(request, connection, onEvent = () => {}) {
  const endpoint = new URL(connection.baseUrl);
  if (endpoint.protocol !== 'http:' || !['127.0.0.1', '[::1]'].includes(endpoint.hostname) || !endpoint.port ||
      endpoint.username || endpoint.password || endpoint.search || endpoint.hash ||
      !/^\/openrouter\/api\/v1\/?$/.test(endpoint.pathname) || !connection.apiKey) {
    throw new Error('Replay requires the local credential service; direct upstream requests are forbidden');
  }
  assert.equal(request.method, 'POST');
  const requested = new URL(request.url ?? connection.baseUrl.replace(/\/$/, '') + '/chat/completions');
  const route = requested.pathname.replace(/^\/openrouter\/api\/v1/, '');
  if (requested.search || requested.hash || !['/chat/completions', '/responses'].includes(route)) {
    throw new Error('Only approved OpenRouter inference routes may be replayed');
  }
  const started = performance.now();
  const elapsed = () => Math.round(performance.now() - started);
  const redact = value => value.replaceAll(connection.apiKey, '[REDACTED]').slice(0, 1024);
  const fields = (value, keys) => Object.fromEntries(keys.flatMap(key => {
    const item = value?.[key];
    return typeof item === 'string' ? [[key, redact(item)]] :
      typeof item === 'boolean' || typeof item === 'number' ? [[key, item]] : [];
  }));
  const timing = { headers_ms: null, first_byte_ms: null, last_byte_ms: null, last_event_ms: null,
    last_non_error_event_ms: null, error_ms: null, error_gap_ms: null, stream_end_ms: null,
    max_byte_gap_ms: 0, max_event_gap_ms: 0, comment_count: 0, event_count: 0, byte_count: 0 };
  const result = { client: 'Node native fetch; no Pi or OpenAI SDK', node_version: process.versions.node,
    request_body_sha256: hash(JSON.stringify(request.body)), timing, event_trace: [], event_trace_dropped: 0,
    raw_text: '', done_received: false };
  const signal = AbortSignal.timeout(900000);
  let buffer = '', data = [];
  function dispatch() {
    if (!data.length) return;
    const text = data.join('\n');
    data = [];
    if (text.trim() === '[DONE]') { result.done_received = true; return; }
    let event;
    try { event = JSON.parse(text); } catch { result.invalid_json_events = (result.invalid_json_events ?? 0) + 1; return; }
    const now = elapsed(), gap = now - (timing.last_event_ms ?? timing.headers_ms);
    timing.max_event_gap_ms = Math.max(timing.max_event_gap_ms, gap);
    timing.event_count++;
    timing.last_event_ms = now;
    Object.assign(result, fields(event, ['id', 'model', 'provider']));
    if (event.response) {
      Object.assign(result, fields(event.response, ['id', 'model', 'provider']));
      if (typeof event.response.status === 'string') result.response_status = redact(event.response.status);
    }
    const usage = event.usage ?? event.response?.usage;
    if (usage) result.usage = usage;
    const error = event.error ?? event.response?.error ?? (event.type === 'error' ? event : null);
    if (error) {
      result.error = { ...fields(error, ['code', 'message', 'type']),
        ...fields(error.metadata, ['error_type', 'provider_code', 'provider_name']),
        ...fields(event, ['error_type']), ...fields(event.response, ['error_type']) };
      timing.error_ms = now;
      timing.error_gap_ms = now - (timing.last_non_error_event_ms ?? timing.headers_ms);
    } else if (!result.error) timing.last_non_error_event_ms = now;
    const body = event.debug?.echo_upstream_body;
    if (body) {
      const format = body.text?.format ?? body.response_format?.json_schema;
      result.upstream_request = { ...fields(body, ['model', 'stream', 'store', 'max_output_tokens', 'max_tokens']),
        body_sha256: hash(JSON.stringify(body)), reasoning: fields(body.reasoning, ['effort', 'summary']),
        ...(format?.schema ? { schema_sha256: hash(JSON.stringify(format.schema)), format: fields(format, ['type', 'strict']) } : {}) };
    }
    let contentChars = 0, reasoningChars = 0;
    if (event.type === 'response.output_text.delta' && typeof event.delta === 'string') {
      result.raw_text += event.delta;
      contentChars += event.delta.length;
    }
    if (['response.reasoning_summary_text.delta', 'response.reasoning_text.delta'].includes(event.type) && typeof event.delta === 'string') {
      reasoningChars += event.delta.length;
    }
    const deltaFields = new Set();
    for (const choice of event.choices ?? []) {
      if (choice.finish_reason) result.finish_reason = choice.finish_reason;
      for (const field of Object.keys(choice.delta ?? {})) deltaFields.add(field);
      if (typeof choice.delta?.content === 'string') { result.raw_text += choice.delta.content; contentChars += choice.delta.content.length; }
      if (typeof choice.delta?.reasoning === 'string') reasoningChars += choice.delta.reasoning.length;
    }
    const trace = { at_ms: now, gap_ms: gap, kind: error ? 'error' : body ? 'debug' : 'response',
      ...fields(event, ['type']),
      delta_fields: [...deltaFields].slice(0, 32).map(redact), content_chars: contentChars, reasoning_chars: reasoningChars,
      ...(usage ? { usage } : {}), ...(error ? { error: result.error } : {}) };
    if (result.event_trace.length < 256) result.event_trace.push(trace); else result.event_trace_dropped++;
    onEvent(trace);
  }
  function line(value) {
    if (!value) dispatch();
    else if (value.startsWith('data:')) data.push(value.slice(5).replace(/^ /, ''));
    else if (value.startsWith(':')) timing.comment_count++;
  }
  function consume() {
    let end;
    while ((end = buffer.indexOf('\n')) >= 0) {
      line(buffer.slice(0, end).replace(/\r$/, ''));
      buffer = buffer.slice(end + 1);
    }
  }
  try {
    const response = await fetch(connection.baseUrl.replace(/\/$/, '') + route, {
      method: request.method, headers: { ...request.headers, authorization: `Bearer ${connection.apiKey}` },
      body: JSON.stringify(request.body), signal, redirect: 'error',
    });
    result.http_status = response.status;
    timing.headers_ms = elapsed();
    if (!response.headers.get('content-type')?.includes('text/event-stream')) {
      const text = await response.text();
      result.non_stream_body_sha256 = hash(text);
      result.unexpected_non_stream_response = true;
    } else {
      const decoder = new TextDecoder();
      for await (const chunk of response.body) {
        const now = elapsed();
        timing.max_byte_gap_ms = Math.max(timing.max_byte_gap_ms, now - (timing.last_byte_ms ?? timing.headers_ms));
        timing.first_byte_ms ??= now;
        timing.last_byte_ms = now;
        timing.byte_count += chunk.byteLength;
        buffer += decoder.decode(chunk, { stream: true });
        consume();
      }
      buffer += decoder.decode();
      consume();
      if (buffer) line(buffer.replace(/\r$/, ''));
      dispatch();
    }
    timing.stream_end_ms = elapsed();
  } catch (error) {
    result.transport_error = { phase: timing.headers_ms === null ? 'headers' : 'body',
      ...fields(error, ['name', 'code', 'message']), cause: fields(error.cause, ['name', 'code', 'message']) };
  }
  result.local_abort = signal.aborted;
  result.elapsed_ms = elapsed();
  return result;
}

async function main() {
  assert.deepEqual(process.argv.slice(2), ['--send']);
  const here = new URL('./', import.meta.url), root = new URL('../../../../', here);
  const prior = JSON.parse(fs.readFileSync(new URL('../diagnostic-retry-v2/result.json', here)));
  const ledger = JSON.parse(fs.readFileSync(new URL('budget-ledger.json', root)));
  const reservation = ledger.entries.at(-1);
  assert.equal(reservation.reservation_id, 'frontier-asv6.48-muse-pi-bypass-v1');
  assert.equal(reservation.kind, 'subject_diagnostic_reservation');
  assert.equal(reservation.reserved_maximum_charge_cents, 100);
  assert.ok(ledger.actual_spend_cents + ledger.outstanding_commitments_cents + ledger.reserved_remaining_work_cents <= ledger.lifetime_cap_cents);
  const directory = process.env.PI_CODING_AGENT_DIR || join(homedir(), '.pi', 'agent');
  let connection;
  try {
    const models = JSON.parse(fs.readFileSync(join(directory, 'models.json')));
    const auth = JSON.parse(fs.readFileSync(join(directory, 'auth.json')));
    const provider = models.providers.openrouter;
    assert.equal(auth.openrouter.type, 'api_key');
    assert.equal(provider.apiKey, auth.openrouter.key);
    connection = { baseUrl: provider.baseUrl, apiKey: auth.openrouter.key };
  } catch { throw new Error('Missing selected local credential-service configuration'); }
  const save = (name, value) => fs.writeFileSync(new URL(name, here), JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
  save('attempt.json', { started_at_utc: new Date().toISOString(), reservation_id: reservation.reservation_id,
    note_id: 'N031', source: '../diagnostic-retry-v2/result.json', request_body_sha256: hash(JSON.stringify(prior.request.body)),
    replay_source_sha256: hash(fs.readFileSync(new URL('replay.mjs', here))), direct_meta_authorized: false });
  const trace = fs.openSync(new URL('events.jsonl', here), 'wx');
  let count = 0;
  const result = await replay(prior.request, connection, event => {
    fs.writeSync(trace, JSON.stringify(event) + '\n');
    if (++count <= 16 || event.error || event.usage) console.log(JSON.stringify(event));
  });
  fs.closeSync(trace);
  save('result.json', result);
  console.log(JSON.stringify({ finished: true, elapsed_ms: result.elapsed_ms, error: result.error,
    transport_error: result.transport_error, usage: result.usage, timing: result.timing, done_received: result.done_received }));
  if (result.error || result.transport_error || !result.done_received) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(() => { console.error('Replay failed; inspect saved diagnostic files. No credentials printed.'); process.exitCode = 1; });
}
