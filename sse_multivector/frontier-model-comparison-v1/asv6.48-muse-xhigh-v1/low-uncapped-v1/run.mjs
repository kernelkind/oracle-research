import fs from 'node:fs';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { replay } from '../pi-bypass-v1/replay.mjs';

const here = new URL('./', import.meta.url);
const hash = value => createHash('sha256').update(value).digest('hex');
const prior = JSON.parse(fs.readFileSync(new URL('../no-token-limit-v1/attempt.json', here)));
const request = structuredClone(prior.request);
request.body.reasoning.effort = 'low';

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 1 && args[0] === '--preview') {
    console.log(JSON.stringify({ request, timeout_seconds: 900, source_body_sha256: hash(JSON.stringify(prior.request.body)) }));
    return;
  }
  assert.deepEqual(args, ['--send']);
  const ledger = JSON.parse(fs.readFileSync(new URL('../../../../budget-ledger.json', here)));
  const reservation = ledger.entries.at(-1);
  assert.equal(reservation.reservation_id, 'frontier-asv6.48-muse-low-uncapped-v1');
  assert.equal(reservation.kind, 'subject_diagnostic_reservation');
  assert.equal(reservation.reserved_maximum_charge_cents, 100);
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
  const save = (name, value) => fs.writeFileSync(new URL(name, here), JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
  save('attempt.json', { started_at_utc: new Date().toISOString(), reservation_id: reservation.reservation_id,
    note_id: 'N031', change: 'Change only reasoning.effort from xhigh to low; preserve the uncapped request', request,
    request_body_sha256: hash(JSON.stringify(request.body)), source_body_sha256: hash(JSON.stringify(prior.request.body)),
    run_source_sha256: hash(fs.readFileSync(new URL('run.mjs', here))), direct_meta_authorized: false });
  const trace = fs.openSync(new URL('events.jsonl', here), 'wx');
  let count = 0;
  const result = await replay(request, connection, event => {
    fs.writeSync(trace, JSON.stringify(event) + '\n');
    if (++count <= 8 || event.kind === 'debug' || event.error || event.usage) console.log(JSON.stringify(event));
  });
  fs.closeSync(trace);
  save('result.json', result);
  console.log(JSON.stringify({ finished: true, elapsed_ms: result.elapsed_ms, error: result.error,
    transport_error: result.transport_error, usage: result.usage, upstream_request: result.upstream_request,
    timing: result.timing, done_received: result.done_received }));
  if (result.error || result.transport_error || !result.done_received) process.exitCode = 1;
}

main().catch(() => { console.error('Diagnostic failed; inspect saved artifacts. No credentials printed.'); process.exitCode = 1; });
