import assert from 'node:assert/strict';
import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';

test('diagnostic removes only the API schema from the uncapped request', () => {
  const result = spawnSync(process.execPath, [fileURLToPath(new URL('./run.mjs', import.meta.url)), '--preview'], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  const actual = JSON.parse(result.stdout);
  const prior = JSON.parse(fs.readFileSync(new URL('../no-token-limit-v1/attempt.json', import.meta.url))).request;
  const expected = structuredClone(prior);
  delete expected.body.response_format;
  assert.equal(Object.hasOwn(actual.request.body, 'response_format'), false, 'API schema must be absent');
  assert.equal(Object.hasOwn(actual.request.body, 'max_tokens'), false, 'max_tokens must be absent, not null or replaced');
  assert.deepEqual(actual.request, expected);
  assert.equal(actual.timeout_seconds, 900);
});
