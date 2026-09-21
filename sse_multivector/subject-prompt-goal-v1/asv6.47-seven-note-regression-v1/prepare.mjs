import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const read = p => JSON.parse(fs.readFileSync(path.resolve(dir, p), 'utf8'));
const config = read('../asv6.47-diverse-v1/config.json');
const prior = read('../asv6.47-diverse-v1/cases.json');
const prompt = fs.readFileSync(prior.prompt_path, 'utf8');
if (crypto.createHash('sha256').update(prompt).digest('hex') !== prior.prompt_sha256)
  throw new Error('Approved ASv6.47 changed');
const notes = read('../../mask-prompt-goal-v1/asv6.37-corpus-ten-v1/notes.json').notes
  .filter(n => !['N065', 'N031', 'N080'].includes(n.id));
if (notes.length !== 7) throw new Error('Expected exactly seven remaining notes');
config.prompts = notes.map(n => ({prompt_id: n.id, text: `${prompt}\n<post>\n${n.text}\n</post>`}));
const cases = {
  ...prior,
  scope: 'Exactly seven fresh isolated Astra-low calls, one per remaining original ten-note sample member. ASv6.47, schema and note texts unchanged. No baseline reruns or masks.',
  baseline_directories: ['../asv6.40.1-ten-note-regression-v1', '../../mask-prompt-goal-v1/asv6.37-corpus-ten-v1'],
  selection: 'All seven original sample notes not yet tested with ASv6.47: N004, N038, N094, N096, N061, N029, N052.',
  checks: ['Retention of enumerated finer subjects', 'Useful broader headings without prescribing a canonical tree', 'Source grounding, references, rhetoric and quantities', 'Opaque names and identifiers are not invented literal subjects', 'Compare semantic coverage to saved outputs without rerunning baselines'],
  limits: 'One fresh output per note is a qualitative regression check, not a reliability estimate or unseen holdout. Older prompt comparisons do not isolate construction order.',
  cases: notes
};
for (const [name, data] of [['config.json', config], ['cases.json', cases]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({calls: config.prompts.map(p => p.prompt_id), model: config.model, effort: config.reasoning_effort}));
