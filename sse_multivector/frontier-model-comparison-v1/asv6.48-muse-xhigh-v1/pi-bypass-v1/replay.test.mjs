import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { test } from 'node:test';
import { replay } from './replay.mjs';

const key = 'LOCAL_TEST_CAPABILITY';
const request = { method: 'POST', headers: { accept: 'application/json', 'content-type': 'application/json', authorization: '[REDACTED]' },
  body: { model: 'meta/muse-spark-1.3-contributor', messages: [{ role: 'user', content: 'test prompt' }],
    stream: true, reasoning: { effort: 'xhigh' }, max_tokens: 32768, debug: { echo_upstream_body: true } } };

test('raw HTTP replay preserves the request, distinguishes upstream silence, and reads usage after an error', async t => {
  const requests = [];
  const server = createServer(async (req, res) => {
    let body = '';
    for await (const chunk of req) body += chunk;
    requests.push({ url: req.url, body, authorization: req.headers.authorization });
    res.writeHead(200, { 'content-type': 'text/event-stream' });
    for (const event of [
      { id: 'gen-test', provider: 'Meta', choices: [{ delta: { reasoning: 'do-not-save-private-reasoning' } }] },
      { error: { code: 502, message: `Network connection lost. ${key}`, metadata: {
        error_type: 'provider_unavailable', provider_code: 'disconnect', raw: 'do-not-save-raw-body' } },
        choices: [{ delta: {}, finish_reason: 'error' }] },
      { choices: [], usage: { cost: 0, prompt_tokens: 3, completion_tokens: 1 } },
    ]) {
      res.write(': OPENROUTER PROCESSING\n\n');
      await new Promise(resolve => setTimeout(resolve, 25));
      res.write(`data: ${JSON.stringify(event)}\n\n`);
    }
    res.end('data: [DONE]\n\n');
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => { server.closeAllConnections(); server.close(); });
  const events = [];
  const result = await replay(request, { baseUrl: `http://127.0.0.1:${server.address().port}/openrouter/api/v1`, apiKey: key }, event => events.push(event));
  assert.deepEqual(requests, [{ url: '/openrouter/api/v1/chat/completions', body: JSON.stringify(request.body), authorization: `Bearer ${key}` }]);
  assert.equal(result.http_status, 200);
  assert.equal(result.error.code, 502);
  assert.equal(result.error.error_type, 'provider_unavailable');
  assert.equal(result.error.provider_code, 'disconnect');
  assert.equal(result.usage.cost, 0);
  assert.equal(result.done_received, true);
  assert.equal(result.finish_reason, 'error');
  assert.ok(result.timing.stream_end_ms >= result.timing.error_ms);
  assert.ok(result.timing.error_gap_ms >= 15);
  assert.equal(result.timing.comment_count, 3);
  assert.equal(events.length, 3);
  assert.equal(events[0].reasoning_chars, 'do-not-save-private-reasoning'.length);
  assert.equal(result.transport_error, undefined);
  const saved = JSON.stringify({ result, events });
  for (const secret of [key, 'do-not-save-private-reasoning', 'do-not-save-raw-body']) assert.ok(!saved.includes(secret));
});

test('raw replay refuses direct upstream addresses', async () => {
  for (const baseUrl of ['https://api.meta.ai/v1', 'https://openrouter.ai/api/v1', 'http://127.0.0.1:9/wrong']) {
    await assert.rejects(replay(request, { baseUrl, apiKey: key }), /local credential service/);
  }
});

test('local socket loss is recorded as transport failure, not an upstream SSE error', async t => {
  let attempts = 0;
  const server = createServer((req, res) => {
    attempts++;
    req.resume();
    res.writeHead(200, { 'content-type': 'text/event-stream' });
    res.write('data: {"id":"gen-broken","choices":[]}\n\n');
    setTimeout(() => res.destroy(), 30);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => { server.closeAllConnections(); server.close(); });
  const result = await replay(request, { baseUrl: `http://127.0.0.1:${server.address().port}/openrouter/api/v1`, apiKey: key });
  assert.equal(attempts, 1);
  assert.equal(result.error, undefined);
  assert.equal(result.transport_error.phase, 'body');
  assert.equal(result.done_received, false);
  assert.equal(result.local_abort, false);
  assert.equal(result.timing.stream_end_ms, null);
});

test('Responses replay selects the approved route and reads lifecycle, text, debug and usage without retaining reasoning', async t => {
  let path;
  const server = createServer((req, res) => {
    path = req.url;
    req.resume();
    res.writeHead(200, { 'content-type': 'text/event-stream' });
    for (const event of [
      { type: 'response.created', response: { id: 'gen-responses', status: 'in_progress' } },
      { type: 'response.debug', debug: { echo_upstream_body: { model: 'muse-spark-1.3-contributor',
        stream: true, reasoning: { effort: 'xhigh', summary: 'auto' }, input: 'private prompt' } } },
      { type: 'response.reasoning_summary_text.delta', delta: 'private reasoning summary' },
      { type: 'response.output_text.delta', delta: '{"subjects":[]}' },
      { type: 'response.output_text.done', text: '{"subjects":[]}' },
      { type: 'response.completed', response: { id: 'gen-responses', status: 'completed',
        output: [{ encrypted_content: 'private encrypted reasoning' }], usage: { input_tokens: 3, output_tokens: 8, cost: 0.01 } } },
    ]) res.write(`data: ${JSON.stringify(event)}\n\n`);
    res.end();
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => { server.closeAllConnections(); server.close(); });
  const baseUrl = `http://127.0.0.1:${server.address().port}/openrouter/api/v1`;
  const result = await replay({ ...request, url: baseUrl + '/responses' }, { baseUrl, apiKey: key });
  assert.equal(path, '/openrouter/api/v1/responses');
  assert.equal(result.id, 'gen-responses');
  assert.equal(result.response_status, 'completed');
  assert.equal(result.raw_text, '{"subjects":[]}');
  assert.equal(result.usage.cost, 0.01);
  assert.equal(result.upstream_request.reasoning.effort, 'xhigh');
  assert.equal(result.event_trace[2].reasoning_chars, 'private reasoning summary'.length);
  assert.equal(result.done_received, false);
  for (const secret of ['private prompt', 'private reasoning summary', 'private encrypted reasoning']) {
    assert.ok(!JSON.stringify(result).includes(secret));
  }
});

test('Responses replay records nested terminal failure and refuses unapproved routes', async t => {
  const server = createServer((req, res) => {
    req.resume();
    res.writeHead(200, { 'content-type': 'text/event-stream' });
    res.end(`data: ${JSON.stringify({ type: 'response.failed', response: { id: 'gen-failed', status: 'failed',
      error_type: 'provider_unavailable', error: { code: 'server_error', message: `Network connection lost. ${key}` },
      usage: { cost: 0 } } })}\n\n`);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => { server.closeAllConnections(); server.close(); });
  const baseUrl = `http://127.0.0.1:${server.address().port}/openrouter/api/v1`;
  const result = await replay({ ...request, url: baseUrl + '/responses' }, { baseUrl, apiKey: key });
  assert.equal(result.response_status, 'failed');
  assert.equal(result.error.error_type, 'provider_unavailable');
  assert.equal(result.error.code, 'server_error');
  assert.equal(result.usage.cost, 0);
  assert.ok(result.timing.error_ms !== null);
  assert.ok(!JSON.stringify(result).includes(key));
  await assert.rejects(replay({ ...request, url: baseUrl + '/generation?id=x' }, { baseUrl, apiKey: key }), /route/);
});
