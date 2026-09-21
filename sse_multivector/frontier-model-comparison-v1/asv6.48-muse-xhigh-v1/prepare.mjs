import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const read = p => JSON.parse(fs.readFileSync(path.resolve(dir, p), 'utf8'));
const config = read('../asv6.48-muse-v1/muse-config.json');
const cases = read('../asv6.48-muse-v1/cases.json');
assert.equal(config.prompts.length, 10);
assert.equal(config.reasoning_effort, 'low');
config.reasoning_effort = 'xhigh';
config.max_output_tokens = 32768;
config.timeout_seconds = 900;
cases.reasoning_effort = 'xhigh';
cases.max_output_tokens_per_call = config.max_output_tokens;
cases.timeout_seconds_per_call = config.timeout_seconds;
cases.scope = 'Ten Muse xhigh calls on the exact saved ASv6.48 inputs/schema, compared with saved Muse low and Astra low. No new low-effort calls, prompt changes, masks or automatic retries.';
cases.changes_from_muse_low = {
  reasoning_effort: ['low', 'xhigh'],
  max_output_tokens: [8192, 32768],
  timeout_seconds: [600, 900],
};
cases.limits = 'One output per configuration per note; exploratory, not a reliability ranking. Muse xhigh has a larger output ceiling and timeout to accommodate additional reasoning. All saved low-effort outputs ended normally, without truncation. Astra low and Muse reasoning levels are not equivalent compute budgets.';
cases.muse_low_directory = '../asv6.48-muse-v1';
const preview = {provider: config.provider, model: config.model, reasoning: config.reasoning_effort,
  prompt: config.prompts[0].text, schema: config.output_schema,
  timeout_seconds: config.timeout_seconds, max_output_tokens: config.max_output_tokens};
for (const [name, value] of [['muse-config.json', config], ['cases.json', cases], ['preview-request.json', preview]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(value, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({calls: config.prompts.length, reasoning: config.reasoning_effort,
  model: config.model, max_output_tokens: config.max_output_tokens, sent: false}));
