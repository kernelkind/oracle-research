import assert from 'node:assert/strict';
import { copyFile, mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { test } from 'node:test';

const oracle = fileURLToPath(new URL('../../', import.meta.url));

test('frozen comparison help uses the shared runner installation', () => {
  const result = spawnSync('bash', [join(oracle, 'sse_multivector/run-frontier-comparison.sh'), '--help'], {
    encoding: 'utf8', timeout: 10000,
    env: { ...process.env, EXPERIMENT_RUNNER_ROOT: join(oracle, '../experiment-runner') },
  });
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Frozen extraction adapter/);
  assert.match(result.stdout, /ASv6\.23/);
});

for (const layout of ['nested', 'sibling']) {
  test(`frontier module resolves a ${layout} experiment-runner checkout`, async t => {
    const root = await mkdtemp(join(tmpdir(), 'oracle-frontier-location-'));
    t.after(() => rm(root, { recursive: true, force: true }));
    const oracle = join(root, 'oracle');
    const adapter = join(oracle, 'sse_multivector/frontier_runner/_shared.mjs');
    const runner = join(layout === 'nested' ? oracle : root, 'experiment-runner');
    const implementation = join(runner, 'experiment_runner/frontier_runner/model.mjs');
    await mkdir(dirname(adapter), { recursive: true });
    await mkdir(dirname(implementation), { recursive: true });
    await writeFile(implementation, '// Location fixture; never executed.\n');
    await copyFile(new URL('_shared.mjs', import.meta.url), adapter);
    const env = { ...process.env };
    delete env.EXPERIMENT_RUNNER_ROOT;
    const result = spawnSync(process.execPath, ['--input-type=module', '-e',
      `import { shared } from ${JSON.stringify(pathToFileURL(adapter).href)}; process.stdout.write(shared('model.mjs'));`],
    { encoding: 'utf8', env, timeout: 10000 });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stdout, pathToFileURL(implementation).href);
  });
}
