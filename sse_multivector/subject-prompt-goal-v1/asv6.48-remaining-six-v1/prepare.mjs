import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const read = p => JSON.parse(fs.readFileSync(path.resolve(dir, p), 'utf8'));
const config = read('../asv6.48-probe-v1/config.json');
const prior = read('../asv6.48-probe-v1/cases.json');
const notes = read('../../mask-prompt-goal-v1/asv6.37-corpus-ten-v1/notes.json').notes
  .filter(n => !['N096', 'N029', 'N080', 'N065'].includes(n.id));
assert.equal(notes.length, 6);
const prompt = fs.readFileSync(prior.prompt_path, 'utf8');
assert.equal(crypto.createHash('sha256').update(prompt).digest('hex'), prior.prompt_sha256);
config.prompts = notes.map(n => ({prompt_id: n.id, text: `${prompt}\n<post>\n${n.text}\n</post>`}));
const cases = {
  ...prior,
  scope: 'One fresh isolated Astra-low call for each of the six original sample notes still lacking ASv6.48 outputs. Preserve the previous four notes and all repeats. No prompt edits, baseline reruns or mask work.',
  baselines: [
    {output_path: '../asv6.47-seven-note-regression-v1/run/output.json', note_ids: ['N004', 'N038', 'N094', 'N061', 'N052']},
    {output_path: '../asv6.47-diverse-v1/run/output.json', note_ids: ['N031']}
  ],
  checks: ['Coverage and grounding against full original notes', 'Named hashtags do not become invented literal subjects', 'Broader headings and finer subjects without requiring a canonical tree', 'Compare saved ASv6.47 outputs without rerunning them'],
  limits: 'Previously used development notes, one new output each; not an unseen holdout or reliability estimate.',
  cases: notes
};
for (const [name, data] of [['config.json', config], ['cases.json', cases]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({calls: notes.map(n => n.id), model: config.model, effort: config.reasoning_effort}));
