// Extend the saved uncapped high diagnostic to the other nine notes, without retries.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { homedir } from 'node:os';
import { join } from 'node:path';
import Ajv from '../../../frontier_runner/node_modules/ajv/dist/ajv.js';
import { replay } from '../pi-bypass-v1/replay.mjs';

const here = new URL('./', import.meta.url);
const read = name => JSON.parse(fs.readFileSync(new URL(name, here)));
const hash = value => createHash('sha256').update(value).digest('hex');
const save = (name, value) => fs.writeFileSync(new URL(name, here), JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });

async function main() {
  const source = read('../high-uncapped-v1/attempt.json');
  const cases = read('../cases.json');
  const config = read('../muse-config.json');
  assert.equal(source.note_id, 'N031');
  assert.equal(source.request.body.reasoning.effort, 'high');
  assert.equal(source.request.body.messages.length, 1);
  assert.equal(source.request.body.messages[0].role, 'user');
  for (const key of ['max_tokens', 'max_completion_tokens', 'max_output_tokens']) {
    assert.equal(Object.hasOwn(source.request.body, key), false);
  }
  assert.equal(cases.requests.length, 10);
  assert.equal(new Set(cases.requests.map(c => c.id)).size, 10);
  const requests = cases.requests.map(item => {
    assert.match(item.id, /^N[0-9]{3}$/);
    const prompt = config.prompts.find(p => p.prompt_id === item.id);
    assert.equal(hash(prompt.text), item.prompt_sha256);
    assert.equal(Buffer.byteLength(prompt.text), item.input_bytes);
    if (item.id === 'N031') assert.equal(prompt.text, source.request.body.messages[0].content);
    const request = structuredClone(source.request);
    request.body.messages[0].content = prompt.text;
    return { note_id: item.id, prompt_sha256: item.prompt_sha256, request };
  }).filter(item => item.note_id !== 'N031');
  assert.equal(requests.length, 9);
  const plan = { prompt_version: 'ASv6.48', reasoning_effort: 'high', caller_token_limit: null,
    retry_count: 0, concurrency: 4, timeout_seconds: 900,
    reused: { note_id: 'N031', result_path: '../high-uncapped-v1/result.json' }, requests };
  const validate = new Ajv({ allErrors: true }).compile(source.request.body.response_format.json_schema.schema);
  function assess(note_id, result, result_path, reused = false) {
    const transport_complete = result.http_status === 200 && result.done_received && result.finish_reason === 'stop' &&
      !result.error && !result.transport_error && !result.local_abort;
    let output, schema_valid = false;
    try { output = JSON.parse(result.raw_text); schema_valid = validate(output); } catch { /* Recorded below. */ }
    return { note_id, reused, result_path, generation_id: result.id, transport_complete, schema_valid,
      valid_completion: transport_complete && schema_valid, subject_count: schema_valid ? output.subjects.length : null,
      elapsed_ms: result.elapsed_ms, cost_usd: result.usage?.cost ?? null,
      error: result.error ?? result.transport_error ?? null,
      max_event_gap_ms: result.timing?.max_event_gap_ms, error_gap_ms: result.timing?.error_gap_ms,
      schema_errors: schema_valid ? null : validate.errors ?? 'Invalid JSON', semantic_quality_assessed: false };
  }
  const reused = assess('N031', read(plan.reused.result_path), plan.reused.result_path, true);
  assert.equal(reused.valid_completion, true);
  function collect() {
    const pending = requests.filter(item => !fs.existsSync(new URL(item.note_id + '/assessment.json', here)));
    if (pending.length) {
      console.log(JSON.stringify({ pending: pending.map(item => item.note_id) }));
      return;
    }
    const results = [reused, ...requests.map(item => read(item.note_id + '/assessment.json'))];
    const summary = { total_notes: results.length, new_requests: requests.length, reused_results: 1,
      valid_completions: results.filter(r => r.valid_completion).length,
      transport_failures: results.filter(r => !r.transport_complete).length,
      invalid_outputs: results.filter(r => r.transport_complete && !r.schema_valid).length,
      new_reported_cost_usd: results.filter(r => !r.reused).reduce((sum, r) => sum + (r.cost_usd ?? 0), 0),
      unknown_new_costs: results.filter(r => !r.reused && r.cost_usd === null).length, results };
    save('summary.json', summary);
    console.log(JSON.stringify({ finished: true, ...summary, results: undefined }));
    if (summary.valid_completions !== 10) process.exitCode = 1;
  }
  if (process.argv.length === 3 && process.argv[2] === '--preview') {
    console.log(JSON.stringify(plan));
    return;
  }
  assert.equal(process.argv.length, 3);
  const mode = process.argv[2];
  if (mode === '--collect') { collect(); return; }
  assert.ok(['--send', '--send-remaining'].includes(mode));
  const ledger = read('../../../../budget-ledger.json');
  const reservation = ledger.entries.at(-1);
  assert.equal(reservation.reservation_id, 'frontier-asv6.48-muse-high-ten-note-v1');
  assert.equal(reservation.kind, 'subject_diagnostic_reservation');
  assert.equal(reservation.reserved_maximum_charge_cents, 100);
  assert.equal(reservation.paid_request_count, 9);
  assert.ok(ledger.actual_spend_cents + ledger.outstanding_commitments_cents + ledger.reserved_remaining_work_cents <= ledger.lifetime_cap_cents);
  const directory = process.env.PI_CODING_AGENT_DIR || join(homedir(), '.pi', 'agent');
  let connection;
  try {
    const models = JSON.parse(fs.readFileSync(join(directory, 'models.json')));
    const auth = JSON.parse(fs.readFileSync(join(directory, 'auth.json')));
    assert.equal(auth.openrouter.type, 'api_key');
    assert.equal(models.providers.openrouter.apiKey, auth.openrouter.key);
    connection = { baseUrl: models.providers.openrouter.baseUrl, apiKey: auth.openrouter.key };
  } catch { throw new Error('Missing selected local credential-service configuration'); }
  // Existing per-note directories are exclusive claims, even if an earlier worker is still running.
  if (mode === '--send-remaining') assert.ok(fs.existsSync(new URL('batch-attempt.json', here)));
  save(mode === '--send' ? 'batch-attempt.json' : 'parallel-attempt.json', {
    started_at_utc: new Date().toISOString(), reservation_id: reservation.reservation_id,
    run_source_sha256: hash(fs.readFileSync(new URL('run.mjs', here))),
    replay_source_sha256: hash(fs.readFileSync(new URL('../pi-bypass-v1/replay.mjs', here))), ...plan });
  const existingActive = requests.filter(item => fs.existsSync(new URL(item.note_id + '/', here)) &&
    !fs.existsSync(new URL(item.note_id + '/assessment.json', here))).length;
  assert.ok(existingActive < plan.concurrency);
  const queue = [...requests];
  async function worker() {
    while (queue.length) {
    const item = queue.shift();
    try { fs.mkdirSync(new URL(item.note_id + '/', here)); }
    catch (error) { if (error.code === 'EEXIST') continue; throw error; }
    save(item.note_id + '/attempt.json', { started_at_utc: new Date().toISOString(),
      reservation_id: reservation.reservation_id, ...item, request_body_sha256: hash(JSON.stringify(item.request.body)) });
    console.log(JSON.stringify({ started: item.note_id }));
    const trace = fs.openSync(new URL(item.note_id + '/events.jsonl', here), 'wx');
    let result;
    try {
      result = await replay(item.request, connection, event => {
        fs.writeSync(trace, JSON.stringify(event) + '\n');
      });
    } finally { fs.closeSync(trace); }
    save(item.note_id + '/result.json', result);
    const assessment = assess(item.note_id, result, item.note_id + '/result.json');
    save(item.note_id + '/assessment.json', assessment);
    console.log(JSON.stringify({ finished: item.note_id, ...assessment }));
    }
  }
  await Promise.all(Array.from({ length: plan.concurrency - existingActive }, () => worker()));
  collect();
}

main().catch(() => { console.error('Batch stopped; inspect saved artifacts. No credentials printed.'); process.exitCode = 1; });
