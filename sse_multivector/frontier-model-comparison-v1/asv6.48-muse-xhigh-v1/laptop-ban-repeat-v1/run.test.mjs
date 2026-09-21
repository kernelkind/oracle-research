import assert from 'node:assert/strict';
import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';

test('diagnostic omits the token limit while preserving every other saved request setting', () => {
  const result = spawnSync(process.execPath, [fileURLToPath(new URL('./run.mjs', import.meta.url)), '--preview'], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  const actual = JSON.parse(result.stdout);
  const prior = fs.readFileSync(new URL('../muse/results.jsonl', import.meta.url), 'utf8').trim().split('\n').map(JSON.parse).find(row => row.note_id === 'N065' && row.status === 'succeeded').model_result.request;
  const expected = structuredClone(prior);
  delete expected.body.max_tokens;
  assert.equal(Object.hasOwn(actual.request.body, 'max_tokens'), false, 'max_tokens must be absent, not null or replaced');
  assert.deepEqual(actual.request, expected);
  assert.equal(actual.timeout_seconds, 900);
});
