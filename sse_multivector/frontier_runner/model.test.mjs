import assert from 'node:assert/strict';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';
import { prepare, preview, execute, VERSION } from './model.mjs';

const codex = { provider: 'openai-codex', model: 'gpt-6-astra', reasoning: 'low' };
const openrouter = { provider: 'openrouter', model: 'meta/muse-spark-1.3-contributor', reasoning: 'low', max_output_tokens: 4096 };
const prompt = '  Arbitrary prompt.\r\nKeep {POST}, <tags>, nostr:npub1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqq and 🦉 exactly.\n';
const config = (route = openrouter, extra = {}) => ({ ...route, prompt, ...extra });
const schema = {
  type: 'object', properties: { count: { type: 'integer' }, label: { type: ['string', 'null'] } },
  required: ['count', 'label'], additionalProperties: false,
};
const sse = frames => new Response(frames.map(frame => `data: ${typeof frame === 'string' ? frame : JSON.stringify(frame)}\n\n`).join(''),
  { headers: { 'content-type': 'text/event-stream' } });
const reply = (text, finish = 'stop') => sse([
  { id: 'response-test', model: 'reported-model', provider: 'reported-provider', choices: [{ index: 0, delta: { content: text }, finish_reason: null }] },
  { id: 'response-test', choices: [{ index: 0, delta: {}, finish_reason: finish }],
    usage: { prompt_tokens: 10, completion_tokens: 5, prompt_tokens_details: { cached_tokens: 4 }, completion_tokens_details: { reasoning_tokens: 2 } } },
  '[DONE]',
]);
const run = async (text, extra = {}, finish = 'stop') => execute(await prepare(config(openrouter, extra)), {
  apiKey: 'test-only', fetch: async () => reply(text, finish),
});

for (const route of [codex, openrouter]) {
  test(`${route.provider}: arbitrary prompt is the only message and needs no schema`, async () => {
    const request = await prepare(config(route));
    const result = await preview(request);
    assert.equal(request.prompt, prompt);
    assert.equal(result.prompt, prompt);
    assert.equal(result.network_requests, 0);
    assert.equal(result.credentials_read, false);
    assert.equal(result.body.model, route.model);
    const messages = result.body.input ?? result.body.messages;
    assert.equal(messages.length, 1);
    assert.equal(messages[0].role, 'user');
    assert.equal(typeof messages[0].content === 'string' ? messages[0].content : messages[0].content[0].text, prompt);
    assert.equal(result.body.instructions ?? '', '');
    for (const key of ['tools', 'tool_choice', 'previous_response_id', 'parallel_tool_calls', 'include', 'system']) assert.equal(result.body[key], undefined);
    assert.equal(result.body.response_format, undefined);
    assert.equal(result.body.text, undefined);
    assert.ok(!JSON.stringify(result).includes('helpful assistant'));
  });

  test(`${route.provider}: caller schema is preserved and provider-default adds no reasoning preference`, async () => {
    const result = await preview(await prepare(config(route, { schema, reasoning: 'provider-default' })));
    const format = result.body.text?.format ?? result.body.response_format?.json_schema;
    assert.deepEqual(format, { ...(route.provider === 'openai-codex' ? { type: 'json_schema' } : {}), name: 'output', strict: true, schema });
    assert.equal(result.body.reasoning, undefined);
  });
}

test('plain-text output succeeds without JSON parsing; response and usage provenance survive', async () => {
  const text = 'A normal answer, not JSON.\n';
  const result = await run(text);
  assert.equal(result.valid, true);
  assert.equal(result.raw_text, text);
  assert.equal(result.output, text);
  assert.equal(result.validation_error, null);
  assert.equal(result.runner_version, VERSION);
  assert.equal(result.response_id, 'response-test');
  assert.equal(result.response_metadata.model, 'reported-model');
  assert.equal(result.response_metadata.provider, 'reported-provider');
  assert.equal(result.response_metadata.http_status, 200);
  assert.equal(result.usage.input, 6);
  assert.equal(result.usage.cacheRead, 4);
  assert.equal(result.usage.output, 5);
  assert.equal(result.response_metadata.usage.completion_tokens_details.reasoning_tokens, 2);
  assert.equal(result.http_attempts, 1);
});

test('caller JSON schema validates without coercion, deletion, defaults, or repair', async () => {
  const good = await run('{"count":2,"label":null}', { schema });
  assert.equal(good.valid, true);
  assert.deepEqual(good.output, { count: 2, label: null });
  for (const text of ['{"count":"2","label":null}', '{"count":2}', '{"count":2,"label":null,"extra":1}', '```json\n{"count":2,"label":null}\n```']) {
    const result = await run(text, { schema });
    assert.equal(result.valid, false);
    assert.equal(result.raw_text, text);
    assert.equal(result.http_attempts, 1);
  }
  const numericString = await run('{"count":"2","label":null}', { schema });
  assert.deepEqual(numericString.output, { count: '2', label: null });
});

test('schemas may use arrays, local references, or boolean schemas', async () => {
  const arraySchema = { $schema: 'https://json-schema.org/draft/2020-12/schema', $defs: { item: { type: 'string', minLength: 1 } }, type: 'array', items: { $ref: '#/$defs/item' }, minItems: 1 };
  assert.equal((await run('["arbitrary"]', { schema: arraySchema })).valid, true);
  assert.equal((await run('[""]', { schema: arraySchema })).valid, false);
  assert.equal((await run('42', { schema: true })).valid, true);
  assert.equal((await run('42', { schema: false })).valid, false);
  const out = await preview(await prepare(config(openrouter, { schema: false })));
  assert.equal(out.body.response_format.json_schema.schema, false);
});

test('standard JSON Schema formats are validated instead of ignored', async () => {
  const dateSchema = { type: 'string', format: 'date-time' };
  assert.equal((await run('"2026-09-16T12:00:00Z"', { schema: dateSchema })).valid, true);
  assert.equal((await run('"not a date"', { schema: dateSchema })).valid, false);
});

test('catalog models and supported caller reasoning are not restricted to the extraction baseline', async () => {
  for (const [model, reasoning, effort] of [['gpt-5.6-terra', 'high', 'high'], ['gpt-6-astra', 'max', 'max']]) {
    const result = await preview(await prepare(config({ ...codex, model, reasoning })));
    assert.equal(result.body.model, model);
    assert.deepEqual(result.body.reasoning, { effort });
  }
  await assert.rejects(prepare(config({ ...codex, reasoning: 'off' })), /reasoning/);
  await assert.rejects(prepare(config({ ...codex, reasoning: 'invented' })), /reasoning/);
});

test('invalid requests fail before transport without silently rewriting prompt, model, schema, or caps', async () => {
  for (const extra of [{ stage: 'subjects' }, { messages: [] }, { system: 'extra' }, { tools: [] }, { prompt: '\ud800' }, { prompt: 1 }, { schema: null }, { schema: [] }, { schema: { type: 'invented' } }, { schema: { $ref: 'https://example.com/remote-schema' } }]) {
    await assert.rejects(prepare(config(openrouter, extra)));
  }
  await assert.rejects(prepare(config({ ...codex, model: 'unknown-model' })), /model/i);
  await assert.rejects(prepare(config({ ...openrouter, model: 'anthropic/claude-3-haiku' })), /unsupported.*transport/i);
  await assert.rejects(prepare(config(codex, { max_output_tokens: 100 })), /output.*cap|output.*limit/i);
  await assert.rejects(prepare(config({ ...openrouter, max_output_tokens: undefined })), /max_output_tokens/);
  await assert.rejects(prepare(config({ ...openrouter, max_output_tokens: 0 })), /max_output_tokens/);
  await assert.rejects(prepare(config(openrouter, { timeout_seconds: 0 })), /timeout_seconds/);
  await assert.rejects(prepare(config({ ...codex, provider: 'openai' })), /provider/);
});

test('model IDs must be strings', async () => {
  await assert.rejects(prepare(config({ ...codex, model: ['gpt-6-astra'] })), /model/i);
});

test('asynchronous schema extensions cannot bypass validation', async () => {
  await assert.rejects(prepare(config(openrouter, { schema: { $async: true, type: 'string' } })), /schema/i);
});

test('failures preserve raw text and usage without retrying', async () => {
  const result = await run('partial answer', {}, 'length');
  assert.equal(result.valid, false);
  assert.equal(result.raw_text, 'partial answer');
  assert.equal(result.usage.output, 5);
  assert.equal(result.http_attempts, 1);
  let attempts = 0;
  const failed = await execute(await prepare(config()), { apiKey: 'secret-test-key', fetch: async () => {
    attempts++;
    return new Response('{"error":{"message":"Failure: secret-test-key"}}', { status: 429 });
  } });
  assert.equal(attempts, 1);
  assert.equal(failed.valid, false);
  assert.equal(failed.response_metadata.http_status, 429);
  assert.ok(!JSON.stringify(failed).includes('secret-test-key'));
});

test('chunked multiline SSE preserves native metadata and exact text', async () => {
  const frames = 'data: {"id":"multiline-response",\r\n' +
    'data: "model":"native-model", "provider":"native-provider", "choices":[{"index":0,"delta":{"content":"Hello 🦉"},"finish_reason":null}]}\r\n\r\n' +
    'data: {"choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":3,"completion_tokens":2}}\r\n\r\n' +
    'data: [DONE]\r\n\r\n';
  const bytes = Buffer.from(frames);
  const result = await execute(await prepare(config()), { apiKey: 'test-only', fetch: async () => new Response(new ReadableStream({
    start(controller) {
      for (let offset = 0; offset < bytes.length; offset += 3) controller.enqueue(bytes.subarray(offset, offset + 3));
      controller.close();
    },
  }), { headers: { 'content-type': 'text/event-stream' } }) });
  assert.equal(result.valid, true, result.error);
  assert.equal(result.raw_text, 'Hello 🦉');
  assert.equal(result.response_metadata.id, 'multiline-response');
  assert.equal(result.response_metadata.provider, 'native-provider');
  assert.equal(result.response_metadata.usage.completion_tokens, 2);
});

test('independent executions never supply earlier input or generated output to later calls', async () => {
  await run('previous response marker', { prompt: 'previous prompt marker' });
  const next = await preview(await prepare(config(openrouter, { prompt: 'next prompt' })));
  assert.deepEqual(next.body.messages, [{ role: 'user', content: 'next prompt' }]);
});

test('CLI version and offline preview do not require credentials; execution requires explicit sending', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'model-runner-test-'));
  const cli = new URL('model.mjs', import.meta.url).pathname;
  const env = { PATH: process.env.PATH, HOME: dir };
  try {
    const version = spawnSync(process.execPath, [cli, '--version'], { encoding: 'utf8', env });
    assert.equal(version.status, 0, version.stderr);
    assert.equal(version.stdout.trim(), `${VERSION} pi-ai/0.85.1`);
    const identity = spawnSync(process.execPath, [cli, '--identity'], { encoding: 'utf8', env });
    assert.equal(identity.status, 0, identity.stderr);
    assert.equal(JSON.parse(identity.stdout).runner_version, VERSION);
    assert.match(JSON.parse(identity.stdout).runner_sha256, /^[0-9a-f]{64}$/);
    const result = spawnSync(process.execPath, [cli, 'preview'], { input: JSON.stringify(config(codex)), encoding: 'utf8', env });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(JSON.parse(result.stdout).network_requests, 0);
    const denied = spawnSync(process.execPath, [cli, 'run'], { input: JSON.stringify(config(codex)), encoding: 'utf8', env });
    assert.equal(denied.status, 1);
    assert.match(denied.stderr, /--send/);
    await writeFile(join(dir, 'auth.json'), '{"OPENAI_API_KEY":"must-not-use"}');
    const auth = spawnSync(process.execPath, [cli, 'run', '--send', '--auth-file', join(dir, 'auth.json')], { input: JSON.stringify(config(codex)), encoding: 'utf8', env });
    assert.equal(auth.status, 1);
    assert.ok(!auth.stderr.includes('must-not-use'));
  } finally { await rm(dir, { recursive: true }); }
});
