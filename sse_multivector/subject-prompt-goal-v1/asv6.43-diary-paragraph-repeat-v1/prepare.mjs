import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const read = p => JSON.parse(fs.readFileSync(path.resolve(dir, p), 'utf8'));
const full = read('../asv6.43-probe-v1/config.json');
const short = read('../asv6.43-meals-paragraph-v1/config.json');
const {prompts: fullPrompts, ...settings} = full;
const {prompts: shortPrompts, ...shortSettings} = short;
assert.deepEqual(settings, shortSettings);
const inputs = {
  full: fullPrompts.find(p => p.prompt_id === 'N080').text,
  paragraph: shortPrompts.find(p => p.prompt_id === 'N080-paragraph').text
};
const config = {...settings, run_directory: 'run', prompts: []};
for (const repeat of [2, 3]) {
  for (const condition of ['full', 'paragraph']) {
    config.prompts.push({prompt_id: `N080-${condition}-${repeat}`, text: inputs[condition]});
  }
}
const cases = {
  prompt_version: 'ASv6.43', model: settings.model, reasoning_effort: settings.reasoning_effort,
  scope: 'Two additional isolated calls per condition, using exact saved prompts and settings. Must execute with --repeat. Together with saved outputs this gives three outputs per condition. No other model calls.',
  baseline_directories: ['../asv6.43-probe-v1', '../asv6.43-meals-paragraph-v1'],
  input_sha256: Object.fromEntries(Object.entries(inputs).map(([k, v]) => [k, crypto.createHash('sha256').update(v).digest('hex')])),
  assessment: 'Compare independent Breakfast and Lunch heading coverage, specific meal details and any new unsupported meanings. Do not require identical hierarchy arrangements. This small single-note test cannot isolate input length from context effects or establish corpus-wide reliability.'
};
for (const [name, data] of [['config.json', config], ['cases.json', cases]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({calls: config.prompts.map(p => p.prompt_id), model: settings.model, effort: settings.reasoning_effort}));
