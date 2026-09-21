import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const read = p => JSON.parse(fs.readFileSync(path.resolve(dir, p), 'utf8'));
const config = read('../asv6.47-seven-note-regression-v1/config.json');
const source = read('../../mask-prompt-goal-v1/asv6.37-corpus-ten-v1/notes.json').notes;
const baselines = read('../asv6.47-sampler-v1/sources.json');
const notes = baselines.map(b => source.find(n => n.id === b.id));
assert.equal(notes.length, 3);
assert.ok(notes.every(Boolean));
const promptPath = path.resolve(dir, '../asv6.48/ASv6.48.md');
const prompt = fs.readFileSync(promptPath, 'utf8');
const hash = crypto.createHash('sha256').update(prompt).digest('hex');
assert.equal(hash, 'e1d5740e68b5f5c29e139ad3fbb37839f91784784aaa31b3bdbdc4a829a4bacc');
assert.ok(!prompt.includes('enumerated_subjects'));
delete config.output_schema.properties.enumerated_subjects;
config.output_schema.required = ['subjects'];
config.prompts = notes.map(n => ({prompt_id: n.id, text: `${prompt}\n<post>\n${n.text}\n</post>`}));
const cases = {
  prompt_version: 'ASv6.48', prompt_path: promptPath, prompt_sha256: hash,
  model: config.model, reasoning_effort: config.reasoning_effort,
  scope: 'Three fresh isolated calls, one per approved sampler note. Remove returned enumeration from prompt and schema; preserve model, effort, complete notes, examples and all other hierarchy instructions. No baseline reruns or masks.',
  baselines,
  checks: ['Final subjects array only', 'Compare finer-subject and broader-heading coverage with saved ASv6.47', 'Inspect source grounding and meaningful branch placements', 'Compare output token usage without treating one sample as a reliable cost estimate'],
  limits: 'One call per note cannot establish equivalence or isolate stochastic variation. Without an emitted initial list, preservation from an internal enumeration cannot be directly inspected.',
  cases: notes
};
for (const [name, data] of [['config.json', config], ['cases.json', cases]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({calls: notes.map(n => n.id), model: config.model, effort: config.reasoning_effort, outputKeys: config.output_schema.required}));
