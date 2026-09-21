import assert from 'node:assert/strict';
import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';

test('low control changes only effort in the exact saved uncapped N031 request', () => {
  const result = spawnSync(process.execPath, [fileURLToPath(new URL('./run.mjs', import.meta.url)), '--preview'], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  const actual = JSON.parse(result.stdout);
  const prior = JSON.parse(fs.readFileSync(new URL('../no-token-limit-v1/attempt.json', import.meta.url))).request;
  assert.equal(prior.body.reasoning.effort, 'xhigh');
  assert.equal(actual.request.body.reasoning.effort, 'low');
  const expected = structuredClone(prior);
  expected.body.reasoning.effort = 'low';
  assert.deepEqual(actual.request, expected);
  for (const key of ['max_tokens', 'max_completion_tokens', 'max_output_tokens']) {
    assert.equal(Object.hasOwn(actual.request.body, key), false, key + ' must remain absent');
  }
  assert.equal(actual.timeout_seconds, 900);
});

