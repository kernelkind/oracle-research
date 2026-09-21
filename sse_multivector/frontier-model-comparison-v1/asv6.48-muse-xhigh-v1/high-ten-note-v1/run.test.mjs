import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn, spawnSync } from 'node:child_process';
import { test } from 'node:test';

const here = new URL('./', import.meta.url);
const load = path => JSON.parse(fs.readFileSync(new URL(path, here)));
const pending = ['N004', 'N038', 'N065', 'N080', 'N094', 'N096', 'N061', 'N029', 'N052'];

test('batch preserves the saved uncapped high request and exact prompts, reusing N031', () => {
  const child = spawnSync(process.execPath, [fileURLToPath(new URL('run.mjs', here)), '--preview'], { encoding: 'utf8' });
  assert.equal(child.status, 0, child.stderr);
  const plan = JSON.parse(child.stdout);
  assert.deepEqual(plan.requests.map(item => item.note_id), pending);
  assert.equal(plan.reused.note_id, 'N031');
  assert.equal(plan.reused.result_path, '../high-uncapped-v1/result.json');
  const source = load('../high-uncapped-v1/attempt.json').request;
  const prompts = load('../muse-config.json').prompts;
  for (const item of plan.requests) {
    const expected = structuredClone(source);
    expected.body.messages[0].content = prompts.find(p => p.prompt_id === item.note_id).text;
    assert.deepEqual(item.request, expected);
    for (const key of ['max_tokens', 'max_completion_tokens', 'max_output_tokens']) {
      assert.equal(Object.hasOwn(item.request.body, key), false);
    }
  }
});

for (const mode of ['--send', '--send-remaining']) test(`real batch CLI ${mode} runs concurrently without repeating existing attempts`, async t => {
  const root = fs.mkdtempSync(join(tmpdir(), 'muse-high-batch-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const batch = join(root, 'sse_multivector/frontier-model-comparison-v1/asv6.48-muse-xhigh-v1/high-ten-note-v1');
  fs.mkdirSync(batch, { recursive: true });
  for (const name of ['run.mjs', '../muse-config.json', '../cases.json', '../high-uncapped-v1/attempt.json',
    '../high-uncapped-v1/result.json', '../pi-bypass-v1/replay.mjs']) {
    const destination = join(batch, name);
    fs.mkdirSync(join(destination, '..'), { recursive: true });
    fs.copyFileSync(new URL(name, here), destination);
  }
  fs.mkdirSync(join(root, 'sse_multivector/frontier_runner'), { recursive: true });
  fs.symlinkSync(fileURLToPath(new URL('../../../frontier_runner/node_modules', here)),
    join(root, 'sse_multivector/frontier_runner/node_modules'));
  fs.writeFileSync(join(root, 'budget-ledger.json'), JSON.stringify({ actual_spend_cents: 0,
    outstanding_commitments_cents: 100, reserved_remaining_work_cents: 0, lifetime_cap_cents: 100000,
    entries: [{ reservation_id: 'frontier-asv6.48-muse-high-ten-note-v1', kind: 'subject_diagnostic_reservation',
      reserved_maximum_charge_cents: 100, paid_request_count: 9 }] }));
  const expectedPending = mode === '--send' ? pending : pending.slice(1);
  if (mode === '--send-remaining') {
    fs.writeFileSync(join(batch, 'batch-attempt.json'), '{}');
    fs.mkdirSync(join(batch, 'N004'));
    fs.writeFileSync(join(batch, 'N004/assessment.json'), JSON.stringify({ note_id: 'N004',
      reused: false, valid_completion: true, transport_complete: true, schema_valid: true, cost_usd: 0.001 }));
  }
  const requests = [];
  let active = 0, maxActive = 0;
  const server = createServer(async (req, res) => {
    let body = '';
    for await (const chunk of req) body += chunk;
    requests.push(JSON.parse(body));
    const n = requests.length;
    maxActive = Math.max(maxActive, ++active);
    await new Promise(resolve => setTimeout(resolve, 40));
    res.writeHead(200, { 'content-type': 'text/event-stream' });
    const event = n === 2 ? { error: { code: 502, message: 'Network connection lost.' },
      choices: [{ finish_reason: 'error', delta: {} }] } : { choices: [{ finish_reason: 'stop',
      delta: { content: JSON.stringify(n === 3 ? { wrong: [] } : {
        subjects: [{ number: '1', context: 'Test', subject: 'Test subject' }] }) } }] };
    res.end(`data: ${JSON.stringify({ ...event, id: 'gen-test-' + n, usage: { cost: 0.001 } })}\n\ndata: [DONE]\n\n`);
    active--;
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => { server.closeAllConnections(); server.close(); });
  const credentials = join(root, 'credentials');
  fs.mkdirSync(credentials);
  fs.writeFileSync(join(credentials, 'auth.json'), JSON.stringify({ openrouter: { type: 'api_key', key: 'TEST_CAPABILITY' } }));
  fs.writeFileSync(join(credentials, 'models.json'), JSON.stringify({ providers: { openrouter: {
    apiKey: 'TEST_CAPABILITY', baseUrl: `http://127.0.0.1:${server.address().port}/openrouter/api/v1` } } }));
  const invoke = () => new Promise(resolve => {
    const child = spawn(process.execPath, [join(batch, 'run.mjs'), mode], {
      env: { ...process.env, PI_CODING_AGENT_DIR: credentials } });
    let output = '';
    child.stdout.on('data', data => { output += data; });
    child.stderr.on('data', data => { output += data; });
    child.on('close', code => resolve({ code, output }));
  });
  const first = await invoke();
  assert.equal(first.code, 1, first.output);
  assert.equal(requests.length, expectedPending.length);
  assert.ok(maxActive >= 3 && maxActive <= 4, `expected bounded concurrency, got ${maxActive}`);
  const promptIds = new Map(load('../muse-config.json').prompts.map(p => [p.text, p.prompt_id]));
  assert.deepEqual(requests.map(r => promptIds.get(r.messages[0].content)).sort(), [...expectedPending].sort());
  const summary = JSON.parse(fs.readFileSync(join(batch, 'summary.json')));
  assert.equal(summary.total_notes, 10);
  assert.equal(summary.new_requests, 9);
  assert.equal(summary.valid_completions, 8);
  assert.equal(summary.transport_failures, 1);
  assert.equal(summary.invalid_outputs, 1);
  assert.equal(summary.results.filter(r => r.reused).length, 1);
  assert.ok(!first.output.includes('TEST_CAPABILITY'));
  const second = await invoke();
  assert.equal(second.code, 1);
  assert.equal(requests.length, expectedPending.length, 'a second invocation must not make duplicate requests');
});
