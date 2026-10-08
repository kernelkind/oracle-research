import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { createServer } from 'node:http';
import { test } from 'node:test';

const cli = new URL('model.mjs', import.meta.url).pathname;
const config = { provider: 'openai-codex', model: 'gpt-6-astra', reasoning: 'low', prompt: 'Offline only.' };

for (const environmentBacked of [false, true]) {
test(`OpenRouter uses local Pi configuration (${environmentBacked ? 'environment reference' : 'legacy literal'})`, async t => {
  const home = await mkdtemp(join(tmpdir(), 'oracle-openrouter-service-'));
  t.after(() => rm(home, { recursive: true, force: true }));
  const key = 'LOCAL_OPENROUTER_CAPABILITY';
  const requests = [];
  const server = createServer((request, response) => {
    requests.push({ url: request.url, authorization: request.headers.authorization });
    request.resume();
    response.writeHead(200, { 'content-type': 'text/event-stream' });
    response.end([
      { id: 'test', choices: [{ index: 0, delta: { content: '["bread"]' }, finish_reason: null }] },
      { id: 'test', choices: [{ index: 0, delta: {}, finish_reason: 'stop' }], usage: { prompt_tokens: 1, completion_tokens: 1 } },
      '[DONE]',
    ].map(event => `data: ${typeof event === 'string' ? event : JSON.stringify(event)}\n\n`).join(''));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => { server.closeAllConnections(); server.close(); });
  const baseUrl = `http://127.0.0.1:${server.address().port}/openrouter/api/v1`;
  await writeFile(join(home, 'models.json'), JSON.stringify({ providers: { openrouter: {
    baseUrl, apiKey: environmentBacked ? '$AGENT_OPENROUTER_CAPABILITY' : key,
  } } }));
  await writeFile(join(home, 'auth.json'), environmentBacked ? 'MUST_NOT_READ_NATIVE_AUTH' :
    JSON.stringify({ openrouter: { type: 'api_key', key } }));
  const input = { provider: 'openrouter', model: 'meta/muse-spark-1.3-contributor',
    reasoning: 'low', max_output_tokens: 40, prompt: 'Offline only.' };
  await writeFile(join(home, 'agent-account'), `#!${process.execPath}\n` +
    `const a=process.argv.slice(2);require('node:assert/strict').deepEqual(a.slice(0,3),['exec','pi','--']);\n` +
    `process.execve(a[3],a.slice(3),process.env);\n`, { mode: 0o700 });
  for (const [entry, request, flags] of [
    [cli, input, ['--pi-config']],
    [cli, input, []],
    [cli, { ...input, debug: { echo_upstream_body: true } }, []],
    [new URL('runner.mjs', import.meta.url).pathname,
      { provider: input.provider, model: input.model, reasoning: input.reasoning,
        max_output_tokens: 40, stage: 'masks', text: 'bread', subject: 'bread' }, []],
  ]) {
    const child = spawn(process.execPath, [entry, 'run', '--send', ...flags], {
      env: { ...process.env, PATH: home, PI_CODING_AGENT_DIR: home, OPENROUTER_API_KEY: 'DO_NOT_USE_UPSTREAM_KEY',
        AGENT_OPENROUTER_CAPABILITY: environmentBacked ? key : 'DO_NOT_OVERRIDE_LEGACY_KEY' },
      stdio: ['pipe', 'pipe', 'pipe'], timeout: 10000,
    });
    let stdout = '', stderr = '';
    child.stdout.on('data', chunk => { stdout += chunk; });
    child.stderr.on('data', chunk => { stderr += chunk; });
    child.stdin.end(JSON.stringify(request));
    const status = await new Promise((resolve, reject) => { child.once('error', reject); child.once('close', resolve); });
    assert.equal(status, 0, stderr);
    const result = JSON.parse(stdout);
    assert.equal(result.valid, true, result.error);
    assert.equal(result.request.url, baseUrl + '/chat/completions');
    assert.deepEqual(result.request.body.debug, request.debug);
    if (request.debug) assert.equal(result.timing.event_trace.length, 2);
    assert.ok(!(stdout + stderr).includes(key));
    assert.ok(!(stdout + stderr).includes('DO_NOT_USE_UPSTREAM_KEY'));
    // First request ignores invalid auth.json; subsequent requests work without it.
    if (environmentBacked) await rm(join(home, 'auth.json'), { force: true });
  }
  assert.equal(requests.length, 4);
  assert.ok(requests.every(r => r.url === '/openrouter/api/v1/chat/completions' && r.authorization === `Bearer ${key}`));
});
}

test('OpenRouter environment handoff rejects invalid routing or capabilities without fallback', async t => {
  const home = await mkdtemp(join(tmpdir(), 'oracle-openrouter-refusal-'));
  t.after(() => rm(home, { recursive: true, force: true }));
  const reference = '$AGENT_OPENROUTER_CAPABILITY';
  const local = 'http://127.0.0.1:9/openrouter/api/v1';
  const key = 'LOCAL_SECRET_SENTINEL';
  const input = { provider: 'openrouter', model: 'meta/muse-spark-1.3-contributor', reasoning: 'low', prompt: 'Offline only.' };
  for (const [baseUrl, apiKey, capability] of [
    [local, reference, undefined], [local, reference, ''], [local, reference, 'BAD SECRET'],
    [local, reference, 'BAD\nSECRET'], [local, '$OPENROUTER_API_KEY', key],
    [local, '!echo DO_NOT_EXECUTE', key], [local, '${AGENT_OPENROUTER_CAPABILITY}', key],
    ['https://openrouter.ai/api/v1', reference, key],
    ['http://user:password@127.0.0.1:9/openrouter/api/v1', reference, key],
    [local + '?PRIVATE_QUERY', reference, key], [local + '#PRIVATE_FRAGMENT', reference, key],
    ['http://127.0.0.1:9/main/pi', reference, key],
  ]) {
    await writeFile(join(home, 'models.json'), JSON.stringify({ providers: { openrouter: { baseUrl, apiKey } } }));
    // Even a matching native entry must not rescue a missing variable or an unsupported reference.
    await writeFile(join(home, 'auth.json'), JSON.stringify({ openrouter: { type: 'api_key', key: apiKey } }));
    const env = { ...process.env, HOME: home, PATH: home, PI_CODING_AGENT_DIR: home,
      OPENROUTER_API_KEY: 'UPSTREAM_SECRET', OPENAI_API_KEY: 'OTHER_UPSTREAM_SECRET' };
    delete env.AGENT_OPENROUTER_CAPABILITY;
    if (capability !== undefined) env.AGENT_OPENROUTER_CAPABILITY = capability;
    const result = spawnSync(process.execPath, [cli, 'run', '--send', '--pi-config'], {
      input: JSON.stringify(input), encoding: 'utf8', env, timeout: 10000,
    });
    assert.equal(result.status, 1);
    assert.equal(result.stdout, '');
    assert.match(result.stderr, /Valid local Pi configuration is required/);
    for (const secret of [key, 'UPSTREAM_SECRET', 'PRIVATE_QUERY', 'PRIVATE_FRAGMENT', 'password', 'BAD']) {
      assert.ok(!result.stderr.includes(secret));
    }
  }
});

test('ordinary subscription commands observe headerless SSE through the selected Pi service', async t => {
  const home = await mkdtemp(join(tmpdir(), 'oracle-default-service-'));
  t.after(() => rm(home, { recursive: true, force: true }));
  const key = 'test.' + Buffer.from(JSON.stringify({
    'https://api.openai.com/auth': { chatgpt_account_id: 'local-test' },
  })).toString('base64url') + '.local';
  const calls = join(home, 'launches');
  const unexpected = join(home, 'bearer-export');
  await writeFile(join(home, 'pi'), `#!${process.execPath}\nrequire('node:fs').writeFileSync(${JSON.stringify(unexpected)},'bad');process.exit(1);\n`, { mode: 0o700 });
  await writeFile(join(home, 'agent-account'), `#!${process.execPath}\n` +
    `const a=process.argv.slice(2);require('node:assert/strict').deepEqual(a.slice(0,3),['exec','pi','--']);\n` +
    `require('node:fs').appendFileSync(${JSON.stringify(calls)},'launch\\n');\n` +
    `process.execve(a[3],a.slice(3),{...process.env,PI_CODING_AGENT_DIR:${JSON.stringify(home)}});\n`, { mode: 0o700 });
  const requests = [];
  let scopeReads = 0;
  const server = createServer((request, response) => {
    if (request.url.startsWith('/request-status/scopes?')) {
      assert.equal(request.headers.authorization, `Bearer ${key}`);
      scopeReads++;
      response.setHeader('Content-Type', 'application/json');
      response.end(JSON.stringify({ account_scope: 'account-fixture', transport_scope: 'transport-fixture' }));
      return;
    }
    requests.push({ url: request.url, authorization: request.headers.authorization });
    request.resume();
    const text = '["bread"]';
    const item = { id: 'msg-test', type: 'message', role: 'assistant', status: 'completed',
      content: [{ type: 'output_text', text, annotations: [] }] };
    const result = { id: 'resp-test', model: config.model, status: 'completed', output: [item],
      usage: { input_tokens: 1, output_tokens: 1 } };
    response.writeHead(200);
    response.end([
      { type: 'response.created', response: { id: 'resp-test', status: 'in_progress' } },
      { type: 'response.output_item.added', output_index: 0, item: { ...item, content: [] } },
      { type: 'response.output_text.delta', output_index: 0, content_index: 0, delta: text },
      { type: 'response.output_item.done', output_index: 0, item },
      { type: 'response.completed', response: result },
    ].map(event => `data: ${JSON.stringify(event)}\n\n`).join(''));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => { server.closeAllConnections(); server.close(); });
  const baseUrl = `http://127.0.0.1:${server.address().port}/selected/pi`;
  await writeFile(join(home, 'models.json'), JSON.stringify({ providers: { 'openai-codex': { baseUrl, apiKey: key } } }));
  await writeFile(join(home, 'auth.json'), JSON.stringify({ 'openai-codex': { type: 'api_key', key } }));
  for (const [entry, input] of [
    [cli, config],
    [new URL('runner.mjs', import.meta.url).pathname,
      { provider: config.provider, model: config.model, reasoning: 'low', stage: 'masks', text: 'bread', subject: 'bread' }],
  ]) {
    const child = spawn(process.execPath, [entry, 'run', '--send'], {
      env: { ...process.env, PATH: home, PI_CODING_AGENT_DIR: join(home, 'not-selected-yet') },
      stdio: ['pipe', 'pipe', 'pipe'], timeout: 10000,
    });
    let stdout = '', stderr = '';
    child.stdout.on('data', chunk => { stdout += chunk; });
    child.stderr.on('data', chunk => { stderr += chunk; });
    child.stdin.end(JSON.stringify(input));
    const status = await new Promise((resolve, reject) => { child.on('error', reject); child.on('close', resolve); });
    assert.equal(status, 0, stderr);
    const receipt = JSON.parse(stdout);
    assert.equal(receipt.valid, true, receipt.error);
    assert.equal(receipt.request.url, baseUrl + '/codex/responses');
    assert.equal(receipt.http_attempts, 1);
    assert.equal(receipt.response_metadata.id, 'resp-test');
    assert.ok(receipt.timing.byte_count > 0);
    assert.equal(receipt.timing.event_count, 5);
    assert.ok(!stdout.includes(key));
  }
  assert.equal(requests.length, 2);
  assert.ok(requests.every(request => request.url === '/selected/pi/codex/responses' && request.authorization === `Bearer ${key}`));
  assert.equal(await readFile(calls, 'utf8'), 'launch\nlaunch\n');
  // Exercise the supported experiment CLI and unchanged shell runner, not a fake runner.
  await symlink(process.execPath, join(home, 'node'));
  await writeFile(join(home, 'prompt.txt'), 'Batch request {VALUE}');
  await writeFile(join(home, 'cases.json'), JSON.stringify({ cases: [
    { id: 'one', inputs: { VALUE: 'one' } },
    { id: 'two', inputs: { VALUE: 'two' } },
  ] }));
  const spec = join(home, 'spec.json');
  const experiment = join(home, 'experiment');
  await writeFile(spec, JSON.stringify({
    schema_version: 1,
    prompt: { id: 'service-test-v1', path: 'prompt.txt' },
    dataset: { adapter: 'generic', path: 'cases.json' },
    runner: {
      runner_binary: new URL('../run-model.sh', import.meta.url).pathname,
      provider: config.provider, auth_file: null,
      model: config.model, reasoning_effort: config.reasoning, concurrency: 1,
    },
  }));
  async function runExperiment(args) {
    const child = spawn('python3', ['-B', new URL('../experiment.py', import.meta.url).pathname, ...args], {
      env: { ...process.env, PATH: `${home}:${process.env.PATH}`, PI_CODING_AGENT_DIR: join(home, 'not-selected-yet'),
        ORACLE_EXPERIMENT_BACKOFF_DIRECTORY: join(home, 'backoff') },
      stdio: ['ignore', 'pipe', 'pipe'], timeout: 15000,
    });
    let stdout = '', stderr = '';
    child.stdout.on('data', chunk => { stdout += chunk; });
    child.stderr.on('data', chunk => { stderr += chunk; });
    const status = await new Promise((resolve, reject) => { child.once('error', reject); child.once('close', resolve); });
    assert.ok(!(stdout + stderr).includes(key));
    assert.equal(status, 0, stderr);
  }
  await runExperiment(['prepare', experiment, '--spec', spec, '--history-root', home]);
  assert.equal(requests.length, 2);
  assert.equal(await readFile(calls, 'utf8'), 'launch\nlaunch\n');
  await runExperiment(['run', experiment, '--max-new-attempts', '2']);
  const report = JSON.parse(await readFile(join(experiment, 'report.json'), 'utf8'));
  assert.equal(report.summary.valid, 2);
  assert.equal(report.summary.reused, 0);
  assert.equal(report.summary.failed, 0);
  assert.equal(report.summary.unrun, 0);
  assert.equal(requests.length, 4);
  assert.equal(scopeReads, 2, 'prepared scope reads became model calls');
  assert.ok(requests.every(request => request.url === '/selected/pi/codex/responses' && request.authorization === `Bearer ${key}`));
  assert.equal(await readFile(calls, 'utf8'), 'launch\nlaunch\nlaunch\nlaunch\n');
  await assert.rejects(readFile(unexpected), { code: 'ENOENT' });
});

test('local Pi mode rejects incomplete or non-local configuration without exporting bearer credentials', async t => {
  const home = await mkdtemp(join(tmpdir(), 'oracle-proxy-config-'));
  t.after(() => rm(home, { recursive: true, force: true }));
  const env = { ...process.env, PI_CODING_AGENT_DIR: home, PATH: home };
  const calls = join(home, 'pi-called');
  await writeFile(join(home, 'pi'), `#!${process.execPath}\nrequire('node:fs').writeFileSync(${JSON.stringify(calls)},'bad');\n`, { mode: 0o700 });
  const key = 'LOCAL_SECRET_SENTINEL';
  const models = baseUrl => ({ providers: { 'openai-codex': { baseUrl, apiKey: key } } });
  for (const [modelValue, auth] of [
    [models('https://chatgpt.com/backend-api'), { type: 'api_key', key }],
    [models('http://127.0.0.1:1234/main/pi?SECRET_QUERY'), { type: 'api_key', key }],
    [models('http://127.0.0.1:1234/main/pi'), { type: 'oauth', access: 'UPSTREAM_SECRET' }],
    [models('http://127.0.0.1:1234/main/pi'), { type: 'api_key', key: 'MISMATCH_SECRET' }],
    [{}, { type: 'api_key', key }],
  ]) {
    await writeFile(join(home, 'models.json'), JSON.stringify(modelValue));
    await writeFile(join(home, 'auth.json'), JSON.stringify({ 'openai-codex': auth }));
    const result = spawnSync(process.execPath, [cli, 'run', '--send', '--pi-config'], {
      input: JSON.stringify(config), encoding: 'utf8', env, timeout: 10000,
    });
    assert.equal(result.status, 1);
    assert.equal(result.stdout, '');
    assert.match(result.stderr, /local Pi configuration/);
    for (const secret of [key, 'UPSTREAM_SECRET', 'MISMATCH_SECRET', 'SECRET_QUERY'])
      assert.ok(!result.stderr.includes(secret));
    await assert.rejects(readFile(calls), { code: 'ENOENT' });
  }
  for (const [input, extra] of [
    [config, ['--auth-file', '/does-not-exist']],
    [{ ...config, provider: 'openrouter', model: 'meta/muse-spark-1.3-contributor', max_output_tokens: 40 }, []],
  ]) {
    const result = spawnSync(process.execPath, [cli, 'run', '--send', '--pi-config', ...extra], {
      input: JSON.stringify(input), encoding: 'utf8', env, timeout: 10000,
    });
    assert.equal(result.status, 1);
    assert.equal(result.stdout, '');
    assert.match(result.stderr, /local Pi configuration|--auth-file is no longer supported/);
  }
});
