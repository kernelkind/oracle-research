import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const read = p => JSON.parse(fs.readFileSync(path.resolve(dir, p), 'utf8'));
const cases = read('cases.json');
const config = read('muse-config.json');
const baseline = read('../asv6.48-muse-v1/review.json');
const baselineSummary = read('../asv6.48-muse-v1/summary.json');
const lowConfig = read('../asv6.48-muse-v1/muse-config.json');
const assessment = read('assessment.json');
const receipts = fs.readFileSync(path.join(dir, 'muse/results.jsonl'), 'utf8').trim().split('\n').map(JSON.parse);
const outputs = receipts.filter(r => r.status === 'succeeded').map(r => ({prompt_id: r.note_id, response: r.response}));
assert.equal(receipts.length, 5);
const failures = receipts.filter(r => r.status !== 'succeeded');
assert.equal(failures.length, 2);
assert.deepEqual(failures.map(r => r.note_id), ['N065', 'N031']);
for (const failure of failures) assert.equal(failure.model_result.error, 'Network connection lost.');
assert.equal(outputs.length, 3);
assert.deepEqual(config.prompts, lowConfig.prompts);
assert.deepEqual(config.output_schema, lowConfig.output_schema);
const measures = [];
const charges = [];
const notes = cases.requests.map(c => {
  const old = baseline.notes.find(n => n.id === c.id);
  const row = receipts.find(r => r.job_key === `prompt:${c.id}` && r.status === 'succeeded');
  if (!row) {
    const failed = failures.some(r => r.note_id === c.id);
    const status = failed
      ? 'No completed Muse xhigh answer: the request lost its network connection. Not a subject-quality judgment.'
      : 'Muse xhigh not attempted: the batch was paused after repeated network connection failures.';
    const comment = `${status}\n\nThe low-effort baselines are preserved for reference. Do not compare them against this missing answer.`;
    return {...old, results: [
      {...old.results[0], comment}, {...old.results[1], comment},
      {model: 'Muse xhigh · ASv6.48', output: status, comment},
      {...old.results[2], comment}, {...old.results[3], comment},
      {model: 'Muse xhigh contexts', output: status, comment},
    ]};
  }
  assert.equal(row.status, 'succeeded');
  const result = row.model_result;
  assert.equal(result.valid, true);
  assert.equal(result.http_attempts, 1);
  assert.equal(row.model, cases.model);
  assert.equal(row.reasoning_effort, 'xhigh');
  assert.equal(result.request.body.reasoning.effort, 'xhigh');
  assert.equal(result.request.body.max_tokens, 32768);
  const messages = result.request.body.messages;
  assert.equal(messages.length, 1);
  assert.equal(messages[0].role, 'user');
  assert.equal(messages[0].content, config.prompts.find(p => p.prompt_id === c.id).text);
  assert.equal(crypto.createHash('sha256').update(messages[0].content).digest('hex'), c.prompt_sha256);
  const raw = outputs.find(o => o.prompt_id === c.id).response;
  assert.equal(raw, row.response);
  const subjects = JSON.parse(raw).subjects;
  const seen = new Set();
  for (const s of subjects) {
    assert.ok(!seen.has(s.number));
    const parent = s.number.split('.').slice(0, -1).join('.');
    assert.ok(!parent || seen.has(parent), `Missing parent: ${c.id}/${s.number}`);
    seen.add(s.number);
  }
  const metadata = result.response_metadata;
  assert.ok(Number.isFinite(metadata.usage.cost));
  charges.push({id: c.id, generation_id: metadata.id, provider: metadata.provider, usage: metadata.usage});
  measures.push({id: c.id, subjects: subjects.length, elapsed_seconds: result.elapsed_ms / 1000,
    input_tokens: row.usage.input + row.usage.cacheRead + row.usage.cacheWrite,
    output_tokens_including_reasoning: row.usage.output,
    reasoning_tokens: metadata.usage.completion_tokens_details.reasoning_tokens,
    stop_reason: result.stop_reason});
  const noteAssessment = assessment.notes.find(n => n.id === c.id);
  assert.ok(noteAssessment);
  const comment = noteAssessment.comparison;
  const hierarchy = subjects.map(s => `${'  '.repeat(s.number.split('.').length - 1)}${s.number}  ${s.subject}`).join('\n');
  const contexts = subjects.map(s => `${s.number}  ${s.subject}\n${s.context}`).join('\n\n');
  return {...old, results: [
    {...old.results[0], comment}, {...old.results[1], comment},
    {model: 'Muse xhigh · ASv6.48', output: hierarchy, comment},
    {...old.results[2], comment}, {...old.results[3], comment},
    {model: 'Muse xhigh contexts', output: contexts, comment},
  ]};
});
const totals = Object.fromEntries(['subjects', 'elapsed_seconds', 'input_tokens', 'output_tokens_including_reasoning', 'reasoning_tokens']
  .map(k => [k, measures.reduce((n, m) => n + m[k], 0)]));
const billing = {source: 'OpenRouter usage.cost from saved streamed responses, not SDK catalog estimates.',
  receipt_path: 'muse/results.jsonl', charges,
  provider_reported_successful_charge_usd: charges.reduce((n, c) => n + c.usage.cost, 0),
  unresolved_failed_generations: failures.map(r => ({note_id: r.note_id,
    generation_id: r.model_result.response_id, charge_usd: null,
    reason: 'Network connection lost before usage arrived. Installed credential service explicitly disallows generation lookup (main.go:545); failed cost is not assumed zero.'})),
  total_actual_charge_usd: null};
const completedIds = measures.map(r => r.id);
const baselineRows = baselineSummary.metrics.filter(r => completedIds.includes(r.id));
const baselineTotals = model => Object.fromEntries(['subjects', 'elapsed_seconds', 'input_tokens', 'output_tokens_including_reasoning']
  .map(k => [k, baselineRows.reduce((n, r) => n + r[model][k], 0)]));
const summary = {prompt_version: 'ASv6.48', prompt_sha256: cases.prompt_sha256,
  status: 'paused_after_repeated_network_failures',
  calls: {new_muse_xhigh_attempts: 5, successful_muse_xhigh: 3, failed_attempts: 2, manual_network_retry: 1, new_low_effort: 0},
  completed_note_ids: completedIds, failed_uncompleted_note_ids: ['N031'],
  unattempted_note_ids: cases.requests.map(r => r.id).filter(id => !receipts.some(r => r.note_id === id)),
  exact_inputs_and_schema_verified_for_completed_outputs: true,
  matched_three_note_totals: {astra_low: baselineTotals('astra'), muse_low: baselineTotals('muse'), muse_xhigh: totals},
  metrics: measures, findings: assessment.findings, limitations: cases.limits};
for (const [name, value] of [
  ['review.json', {schema_version: 1, title: 'ASv6.48 · Astra low / Muse low / Muse xhigh', notes}],
  ['summary.json', summary], ['billing.json', billing],
]) fs.writeFileSync(path.join(dir, name), JSON.stringify(value, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({totals: summary.matched_three_note_totals, known_successful_cost_usd: billing.provider_reported_successful_charge_usd, unresolved_failed_charges: failures.length}));
