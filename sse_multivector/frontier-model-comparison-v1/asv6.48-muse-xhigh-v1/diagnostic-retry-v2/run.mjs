// One approved diagnostic retry through the normal launcher; never retries itself.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { prepare, preview } from '../../../frontier_runner/model.mjs';

const here = new URL('./', import.meta.url);
const root = new URL('../../../../', here);
const original = JSON.parse(fs.readFileSync(new URL('../diagnostic-retry-v1/muse/results.jsonl', here), 'utf8')).model_result;
const originalConfig = JSON.parse(fs.readFileSync(new URL('../diagnostic-retry-v1/config.json', here), 'utf8'));
const body = original.request.body;
const config = { provider: 'openrouter', model: body.model, reasoning: body.reasoning.effort,
  prompt: body.messages[0].content, schema: originalConfig.output_schema,
  max_output_tokens: body.max_tokens, timeout_seconds: 900, debug: { echo_upstream_body: true } };
const prepared = await prepare(config);
const wire = await preview(prepared);
assert.deepEqual(wire.body, { ...body, debug: config.debug });
assert.equal(prepared.prompt_sha256, original.prompt_sha256);
assert.equal(prepared.schema_sha256, original.schema_sha256);
assert.equal(prepared.reasoning, 'xhigh');
const save = (name, value) => fs.writeFileSync(new URL(name, here), JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
if (process.argv.length === 2) {
  save('request.json', config);
  save('preview.json', wire);
  console.log(JSON.stringify({ sent: false, note_id: 'N031', only_body_change: 'debug.echo_upstream_body',
    prompt_sha256: prepared.prompt_sha256, schema_sha256: prepared.schema_sha256 }));
} else {
  assert.deepEqual(process.argv.slice(2), ['--send']);
  assert.deepEqual(JSON.parse(fs.readFileSync(new URL('request.json', here))), config);
  const ledger = JSON.parse(fs.readFileSync(new URL('budget-ledger.json', root)));
  const reservation = ledger.entries.at(-1);
  assert.equal(reservation.reservation_id, 'frontier-asv6.48-muse-xhigh-diagnostic-retry-v2');
  assert.equal(reservation.kind, 'subject_diagnostic_reservation');
  assert.equal(reservation.reserved_maximum_charge_cents, 100);
  assert.ok(ledger.actual_spend_cents + ledger.outstanding_commitments_cents + ledger.reserved_remaining_work_cents <= ledger.lifetime_cap_cents);
  save('attempt.json', { note_id: 'N031', started_at_utc: new Date().toISOString(),
    reservation_id: reservation.reservation_id, runner_sha256: wire.runner_sha256 });
  const stdout = fs.openSync(new URL('result.json', here), 'wx');
  const stderr = fs.openSync(new URL('stderr.txt', here), 'wx');
  const child = spawn(fileURLToPath(new URL('sse_multivector/run-model.sh', root)), ['run', '--send'],
    { cwd: fileURLToPath(root), stdio: ['pipe', stdout, stderr] });
  fs.closeSync(stdout);
  fs.closeSync(stderr);
  child.stdin.on('error', () => {});
  child.stdin.end(JSON.stringify(config));
  console.log(JSON.stringify({ started: true, note_id: 'N031', automatic_retries: 0 }));
  const code = await new Promise((resolve, reject) => { child.once('error', reject); child.once('close', resolve); });
  const result = JSON.parse(fs.readFileSync(new URL('result.json', here)));
  assert.deepEqual(result.request.body, wire.body);
  console.log(JSON.stringify({ exit_code: code, valid: result.valid, elapsed_ms: result.elapsed_ms,
    error: result.error, response_metadata: result.response_metadata, timing: result.timing }));
  process.exitCode = code;
}
