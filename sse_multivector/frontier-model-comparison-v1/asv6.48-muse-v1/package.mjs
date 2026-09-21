import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const resolve = p => path.resolve(dir, p);
const read = p => JSON.parse(fs.readFileSync(resolve(p), 'utf8'));
const lines = p => fs.readFileSync(resolve(p), 'utf8').trim().split('\n').map(JSON.parse);
const sha = s => crypto.createHash('sha256').update(s).digest('hex');
const cases = read('cases.json');
const config = read('muse-config.json');
const notes = read(cases.notes_path).notes;
const astra = read(cases.astra_output_path).responses;
const sources = read(cases.astra_sources_path).sources;
const sourceDir = path.dirname(resolve(cases.astra_sources_path));
const muse = read('muse/output.json').responses;
const receipts = lines('muse/results.jsonl');
const assessments = read('assessment.json');
assert.equal(receipts.length, 10, 'Expected exactly ten new calls, no retries');
assert.equal(muse.length, 10);
const hierarchy = subjects => subjects.map(s => `${'  '.repeat(s.number.split('.').length - 1)}${s.number}  ${s.subject}`).join('\n');
const contexts = subjects => subjects.map(s => `${s.number}  ${s.subject}\n${s.context}`).join('\n\n');
const validate = subjects => {
  const seen = new Set();
  for (const s of subjects) {
    assert.ok(!seen.has(s.number), `Duplicate number ${s.number}`);
    const parent = s.number.split('.').slice(0, -1).join('.');
    assert.ok(!parent || seen.has(parent), `Missing preceding parent ${parent}`);
    seen.add(s.number);
  }
};
const metrics = [];
const charges = [];
const review = cases.requests.map(c => {
  const note = notes.find(n => n.id === c.id);
  const saved = sources.find(s => s.id === c.id);
  const old = lines(path.join(sourceDir, path.dirname(saved.output_path), 'results.jsonl'))
    .find(r => r.job_key === `prompt:${saved.prompt_id}` && r.status === 'succeeded');
  const fresh = receipts.find(r => r.job_key === `prompt:${c.id}`);
  assert.equal(fresh.status, 'succeeded');
  assert.equal(fresh.model_result.valid, true);
  assert.equal(fresh.model_result.http_attempts, 1);
  assert.equal(fresh.model, cases.model);
  assert.equal(fresh.reasoning_effort, 'low');
  const body = fresh.model_result.request.body;
  assert.equal(body.messages.length, 1);
  assert.equal(body.messages[0].role, 'user');
  assert.equal(body.messages[0].content, config.prompts.find(p => p.prompt_id === c.id).text);
  assert.equal(sha(body.messages[0].content), c.prompt_sha256);
  assert.equal(fresh.prompt_sha256, old.prompt_sha256);
  assert.equal(fresh.response_schema_sha256, old.response_schema_sha256);
  const a = JSON.parse(astra.find(r => r.prompt_id === c.id).response).subjects;
  const m = JSON.parse(muse.find(r => r.prompt_id === c.id).response).subjects;
  validate(a); validate(m);
  const billed = fresh.model_result.response_metadata;
  assert.ok(Number.isFinite(billed.usage.cost), 'Provider-reported cost missing');
  charges.push({id: c.id, generation_id: billed.id, provider: billed.provider, usage: billed.usage});
  const measure = (r, subjects) => ({
    subjects: subjects.length,
    top_level_headings: subjects.filter(s => !s.number.includes('.')).length,
    elapsed_seconds: r.model_result.elapsed_ms / 1000,
    input_tokens: r.usage.input + r.usage.cacheRead + r.usage.cacheWrite,
    output_tokens_including_reasoning: r.usage.output,
    reasoning_tokens: r.model_result.response_metadata.usage?.completion_tokens_details?.reasoning_tokens
      ?? r.usage.reasoning ?? null,
    stop_reason: r.model_result.stop_reason,
  });
  metrics.push({id: c.id, astra: measure(old, a), muse: measure(fresh, m)});
  const assessment = assessments.notes.find(n => n.id === c.id);
  assert.ok(assessment);
  const comment = `${assessment.comparison}\n\nAstra: ${assessment.astra}\n\nMuse: ${assessment.muse}`;
  return {id: c.id, title: assessment.title, text: note.text, results: [
    {model: 'Astra low · ASv6.48', output: hierarchy(a), comment},
    {model: 'Muse low · ASv6.48', output: hierarchy(m), comment},
    {model: 'Astra contexts', output: contexts(a), comment},
    {model: 'Muse contexts', output: contexts(m), comment},
  ]};
});
const sum = (model, key) => metrics.reduce((n, r) => n + r[model][key], 0);
const totals = Object.fromEntries(['astra', 'muse'].map(model => [model, Object.fromEntries(
  ['subjects', 'elapsed_seconds', 'input_tokens', 'output_tokens_including_reasoning']
    .map(key => [key, sum(model, key)])
)]));
const billing = {source: 'OpenRouter usage.cost in each saved streamed response; not the SDK catalog estimate.',
  receipt_path: 'muse/results.jsonl', charges,
  provider_reported_actual_charge_usd: charges.reduce((n, r) => n + r.usage.cost, 0)};
const summary = {prompt_version: 'ASv6.48', prompt_sha256: cases.prompt_sha256,
  calls: {new_muse: 10, new_astra: 0, reused_astra: 10},
  exact_inputs_and_schema_verified: true, valid_numbering_and_parents: true,
  totals, metrics, findings: assessments.findings, limitations: cases.limits};
for (const [name, value] of [
  ['review.json', {schema_version: 1, title: 'ASv6.48 · Astra versus Muse · ten matched notes', notes: review}],
  ['billing.json', billing], ['summary.json', summary],
]) fs.writeFileSync(resolve(name), JSON.stringify(value, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({totals, provider_reported_charge_usd: billing.provider_reported_actual_charge_usd}));
