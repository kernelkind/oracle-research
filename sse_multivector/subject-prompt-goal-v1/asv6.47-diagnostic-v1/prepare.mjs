import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const read = name => JSON.parse(fs.readFileSync(path.resolve(dir, '../asv6.46-diagnostic-v1', name), 'utf8'));
const config = read('config.json');
const cases = read('cases.json');
const promptPath = path.resolve(dir, '../asv6.47/ASv6.47.md');
const prompt = fs.readFileSync(promptPath, 'utf8');
const hash = crypto.createHash('sha256').update(prompt).digest('hex');
if (hash !== '9dea7a5f59adf5cff3b36d4ccc0a020b7cf6c435f0bcb4988a07937e46809a30')
  throw new Error('Approved ASv6.47 changed');
config.prompts = [{prompt_id: 'N080', text: `${prompt}\n<post>\n${cases.cases[0].text}\n</post>`}];
Object.assign(cases, {
  prompt_version: 'ASv6.47', prompt_path: promptPath, prompt_sha256: hash,
  baseline_directory: '../asv6.46-diagnostic-v1',
  checks: [
    'Initial enumeration captures specific subjects expressed by the note; broader headings are not required there',
    'Hierarchy derives independent Breakfast and Lunch headings from specific meal subjects',
    'Specific entries survive and can appear in multiple applicable branches',
    'Inspect all returned entries and their parent relationships against the source, not only meal headings'
  ],
  limits: 'One diagnostic tests the revised instructions and visible artifacts, not reliability or hidden reasoning. Absence of broad headings in initial enumeration is not itself a failure. No baseline calls, masks, or unrelated prompt changes.'
});
for (const [name, data] of [['config.json', config], ['cases.json', cases]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({calls: 1, model: config.model, effort: config.reasoning_effort}));
