// Non-billable accounting lookup through the same local credential service.
// Only the loopback service capability is read; upstream keys remain service-owned.
import fs from 'node:fs';
import {localPiConnection} from '../../frontier_runner/model.mjs';

try {
  const id = process.argv[2];
  if (!/^gen-[A-Za-z0-9-]+$/.test(id ?? '')) throw new Error();
  const connection = await localPiConnection('openrouter');
  const response = await fetch(`${connection.baseUrl}/generation?id=${encodeURIComponent(id)}`, {
    headers: {Authorization: `Bearer ${connection.apiKey}`}, signal: AbortSignal.timeout(30000),
  });
  if (!response.ok) {
    console.log(JSON.stringify({generation_id: id, http_status: response.status}));
    process.exitCode = 1;
  } else {
    const {data} = await response.json();
    const fields = ['id', 'total_cost', 'cancelled', 'generation_time', 'latency', 'model',
      'provider_name', 'tokens_prompt', 'tokens_completion', 'native_tokens_reasoning', 'finish_reason'];
    const record = Object.fromEntries(fields.map(k => [k, data[k] ?? null]));
    fs.writeFileSync(new URL(`./${id}-billing.json`, import.meta.url), JSON.stringify(record, null, 2) + '\n', {flag: 'wx'});
    console.log(JSON.stringify(record));
  }
} catch {
  console.error('Generation accounting lookup failed; no credentials or response headers were printed.');
  process.exitCode = 1;
}
