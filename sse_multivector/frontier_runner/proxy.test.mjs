import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { createServer } from 'node:http';
import { test } from 'node:test';

const cli = new URL('model.mjs', import.meta.url).pathname;
const config = { provider: 'openai-codex', model: 'gpt-6-astra', reasoning: 'low', prompt: 'Offline only.' };

test('ordinary subscription commands use the selected Pi service without a flag or bearer export', async t => {
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
  const server = createServer((request, response) => {
    requests.push({ url: request.url, authorization: request.headers.authorization });
    request.resume();
    const text = '["bread"]';
    const item = { id: 'msg-test', type: 'message', role: 'assistant', status: 'completed',
      content: [{ type: 'output_text', text, annotations: [] }] };
    const result = { id: 'resp-test', model: config.model, status: 'completed', output: [item],
      usage: { input_tokens: 1, output_tokens: 1 } };
    response.writeHead(200, { 'content-type': 'text/event-stream' });
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
    assert.ok(!stdout.includes(key));
  }
  assert.equal(requests.length, 2);
  assert.ok(requests.every(request => request.url === '/selected/pi/codex/responses' && request.authorization === `Bearer ${key}`));
  assert.equal(await readFile(calls, 'utf8'), 'launch\nlaunch\n');
  // Exercise the real saved-batch CLI and unchanged shell runner, not a fake runner.
  await symlink(process.execPath, join(home, 'node'));
  const batchConfig = join(home, 'batch.json');
  await writeFile(batchConfig, JSON.stringify({
    schema_version: 1, runner_binary: new URL('../run-model.sh', import.meta.url).pathname,
    provider: config.provider, auth_file: null, run_directory: join(home, 'batch-run'),
    model: config.model, reasoning_effort: config.reasoning,
    prompts: [{ prompt_id: 'one', text: 'Batch request one' }, { prompt_id: 'two', text: 'Batch request two' }],
  }));
  const batch = spawn('python3', ['-B', new URL('../extraction_pipeline.py', import.meta.url).pathname,
    'prompt', batchConfig], { env: { ...process.env, PATH: `${home}:${process.env.PATH}` },
    stdio: ['ignore', 'pipe', 'pipe'], timeout: 15000 });
  let batchOut = '', batchErr = '';
  batch.stdout.on('data', chunk => { batchOut += chunk; });
  batch.stderr.on('data', chunk => { batchErr += chunk; });
  const batchStatus = await new Promise((resolve, reject) => { batch.once('error', reject); batch.once('close', resolve); });
  assert.equal(batchStatus, 0, batchErr);
  assert.equal(requests.length, 4);
  assert.ok(requests.every(request => request.url === '/selected/pi/codex/responses' && request.authorization === `Bearer ${key}`));
  assert.equal(await readFile(calls, 'utf8'), 'launch\nlaunch\nlaunch\nlaunch\n');
  assert.ok(!(batchOut + batchErr).includes(key));
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
    assert.match(result.stderr, /--pi-config|--auth-file is no longer supported/);
  }
});
