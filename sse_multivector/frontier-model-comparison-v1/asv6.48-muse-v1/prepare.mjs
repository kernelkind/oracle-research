import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const read = p => JSON.parse(fs.readFileSync(path.resolve(dir, p), 'utf8'));
const sourceDir = path.resolve(dir, '../../subject-prompt-goal-v1/asv6.48-remaining-six-v1');
const source = read(path.join(sourceDir, 'ten-note-sources.json'));
const astra = read(path.join(sourceDir, 'ten-note-output.json'));
const config = read('../../subject-prompt-goal-v1/asv6.48-probe-v1/config.json');
const originalSchema = JSON.stringify(config.output_schema);
config.provider = 'openrouter';
config.model = 'meta/muse-spark-1.3-contributor';
config.auth_file = null;
config.run_directory = 'muse';
config.max_output_tokens = 8192;
config.prompts = source.sources.map(s => {
  const outputPath = path.resolve(sourceDir, s.output_path);
  const batchDir = path.dirname(path.dirname(outputPath));
  const saved = read(path.join(batchDir, 'config.json'));
  assert.equal(JSON.stringify(saved.output_schema), originalSchema);
  assert.equal(saved.reasoning_effort, config.reasoning_effort);
  const job = saved.prompts.find(p => p.prompt_id === s.prompt_id);
  assert.ok(job, `Missing saved input: ${s.id}`);
  assert.ok(astra.responses.find(r => r.prompt_id === s.id));
  return {prompt_id: s.id, text: job.text};
});
assert.equal(config.prompts.length, 10);
const cases = {
  prompt_version: 'ASv6.48', prompt_sha256: source.prompt_sha256,
  scope: 'Ten Muse-low calls, one per original sample note, using exact saved Astra user prompts and output schema. Reuse all ten Astra responses; no new Astra calls, prompt changes, masks or automatic retries.',
  provider: config.provider, model: config.model, reasoning_effort: config.reasoning_effort,
  maximum_calls: 10, max_output_tokens_per_call: config.max_output_tokens,
  credentials: 'Normal launcher uses the local credential service; no raw key or upstream auth-file path.',
  astra_output_path: path.relative(dir, path.join(sourceDir, 'ten-note-output.json')),
  astra_sources_path: path.relative(dir, path.join(sourceDir, 'ten-note-sources.json')),
  notes_path: path.relative(dir, path.resolve(sourceDir, source.notes_path)),
  checks: ['Source grounding and reference resolution', 'Standalone broader subjects and specific-subject coverage', 'Meaningful hierarchy branches without requiring identical trees', 'No invented meanings from opaque identifiers or hashtags', 'Report concrete differences plus measured usage and latency'],
  limits: 'One output per model per note is exploratory, not a reliability ranking. Low reasoning has different implementations across models; the OpenRouter route uses an explicit output cap while Astra subscription did not.',
  requests: config.prompts.map(p => ({id: p.prompt_id, input_bytes: Buffer.byteLength(p.text), prompt_sha256: crypto.createHash('sha256').update(p.text).digest('hex')}))
};
const first = config.prompts[0];
const preview = {provider: config.provider, model: config.model, reasoning: config.reasoning_effort, prompt: first.text, schema: config.output_schema, timeout_seconds: config.timeout_seconds, max_output_tokens: config.max_output_tokens};
for (const [name, data] of [['muse-config.json', config], ['cases.json', cases], ['preview-request.json', preview]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({calls: cases.maximum_calls, model: config.model, effort: config.reasoning_effort, input_bytes: cases.requests.reduce((n, r) => n + r.input_bytes, 0), maximum_output_tokens: cases.maximum_calls * config.max_output_tokens, sent: false}));
