import assert from 'node:assert/strict';
import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';

test('Responses diagnostic preserves the prompt, schema and effective reasoning settings without adding a token cap', () => {
  const r = spawnSync(process.execPath, [fileURLToPath(new URL('./run.mjs', import.meta.url)), '--preview'], { encoding: 'utf8' });
  assert.equal(r.status, 0, r.stderr);
  const actual = JSON.parse(r.stdout);
  const prior = JSON.parse(fs.readFileSync(new URL('../diagnostic-retry-v2/result.json', import.meta.url))).request;
  const b = prior.body;
  assert.equal(actual.request.url, prior.url.replace('/chat/completions', '/responses'));
  assert.deepEqual(actual.request.headers, prior.headers);
  assert.deepEqual(actual.request.body, {
    model: b.model,
    input: b.messages.map(m => ({ type: 'message', role: m.role, content: [{ type: 'input_text', text: m.content }] })),
    text: { format: { type: 'json_schema', ...b.response_format.json_schema } },
    reasoning: { effort: b.reasoning.effort, summary: 'auto' },
    stream: true, store: false, provider: b.provider, debug: b.debug,
  });
  assert.equal(actual.timeout_seconds, 900);
});
