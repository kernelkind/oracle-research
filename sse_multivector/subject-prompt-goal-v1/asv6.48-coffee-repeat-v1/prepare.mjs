import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const read = p => JSON.parse(fs.readFileSync(path.resolve(dir, p), 'utf8'));
const config = read('../asv6.48-probe-v1/config.json');
const prior = read('../asv6.48-probe-v1/cases.json');
const note = read('../asv6.47-diverse-v1/cases.json').cases.find(n => n.id === 'N065');
assert.ok(note);
const prompt = fs.readFileSync(prior.prompt_path, 'utf8');
assert.equal(crypto.createHash('sha256').update(prompt).digest('hex'), prior.prompt_sha256);
config.prompts = [1, 2, 3].map(i => ({prompt_id: `N065-trial-${i}`, text: `${prompt}\n<post>\n${note.text}\n</post>`}));
const cases = {
  ...prior,
  scope: 'Three fresh isolated Astra-low calls on unchanged N065 using unchanged ASv6.48. Compare with three saved ASv6.47 outputs; no baseline reruns, masks or prompt edits.',
  baselines: [
    {output_path: '../asv6.47-diverse-v1/run/output.json', prompt_id: 'N065'},
    {output_path: '../asv6.47-repeat-v1/run/output.json', prompt_id: 'N065-trial-2'},
    {output_path: '../asv6.47-repeat-v1/run/output.json', prompt_id: 'N065-trial-3'}
  ],
  checks: ['Independent Coffee shops heading, not only coffee-shop events', 'Main finer subjects and source grounding', 'Preserve contemplated retaliation versus actual visit and planned withdrawal', 'Output usage compared with saved baseline'],
  limits: 'Three repetitions of one development note do not establish corpus-wide reliability or complete equivalence. Different valid hierarchies are allowed.',
  cases: [note]
};
for (const [name, data] of [['config.json', config], ['cases.json', cases]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({calls: config.prompts.map(p => p.prompt_id), model: config.model, effort: config.reasoning_effort}));
