import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const baseline = path.resolve(dir, '../asv6.43-probe-v1');
const prior = JSON.parse(fs.readFileSync(path.join(baseline, 'cases.json'), 'utf8'));
const note = prior.cases.find(n => n.id === 'N080');
if (!note) throw new Error('Missing original full diary');
const promptPath = path.resolve(dir, '../asv6.44/ASv6.44.md');
const prompt = fs.readFileSync(promptPath, 'utf8');
const promptHash = crypto.createHash('sha256').update(prompt).digest('hex');
if (promptHash !== '56b04406e4bd3ebd373f98723beb1adf60663623681a09142ff49c097871ba97')
  throw new Error('Approved ASv6.44 prompt changed');
const config = JSON.parse(fs.readFileSync(path.join(baseline, 'config.json'), 'utf8'));
config.run_directory = 'run';
config.prompts = [1, 2, 3].map(i => ({prompt_id: `N080-full-${i}`, text: `${prompt}\n<post>\n${note.text}\n</post>`}));
const cases = {
  prompt_version: 'ASv6.44', prompt_path: promptPath, prompt_sha256: promptHash,
  model: config.model, reasoning_effort: config.reasoning_effort,
  scope: 'Three fresh isolated full-diary calls using --repeat. No baseline reruns or mask calls. Only the approved instruction revision changes; preserve full source text, schema and model settings.',
  baseline_directories: ['../asv6.43-probe-v1', '../asv6.43-diary-paragraph-repeat-v1'],
  checks: ['Independent Breakfast and Lunch heading coverage', 'Specific meal details preserved', 'Whole-note coverage, reference resolution and cross-passage meaning preserved', 'Unsupported meanings or hierarchy relations'],
  interpretation: 'Compare the three saved ASv6.43 full-note outputs with these three outputs. Accept alternative valid hierarchies. A difference on one note does not establish general reliability or prove internal passage-by-passage reasoning occurred.',
  cases: [note]
};
for (const [name, data] of [['config.json', config], ['cases.json', cases]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({calls: config.prompts.map(p => p.prompt_id), model: config.model, effort: config.reasoning_effort}));
