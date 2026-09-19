import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';

const cli = new URL('model.mjs', import.meta.url).pathname;
const config = { provider: 'openai-codex', model: 'gpt-6-astra', reasoning: 'low', prompt: 'Offline only.' };

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
    assert.match(result.stderr, /--pi-config/);
  }
});
