import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const read = p => JSON.parse(fs.readFileSync(path.resolve(dir, p), 'utf8'));
const config = read('../asv6.45-diary-v1/config.json');
const prior = read('../asv6.45-diary-v1/cases.json');
const note = prior.cases.find(n => n.id === 'N080');
if (!note) throw new Error('Missing full diary');
const promptPath = path.resolve(dir, '../asv6.46/ASv6.46.md');
const prompt = fs.readFileSync(promptPath, 'utf8');
const hash = crypto.createHash('sha256').update(prompt).digest('hex');
if (hash !== '08ddd1f9debd5935f65fa71d3cb9dc6512e989be639badbe1a939232255a8895')
  throw new Error('Approved ASv6.46 changed');
config.output_schema = read('../asv6.46/output-schema.json');
config.prompts = [{prompt_id: 'N080', text: `${prompt}\n<post>\n${note.text}\n</post>`}];
const cases = {
  prompt_version: 'ASv6.46', prompt_path: promptPath, prompt_sha256: hash,
  model: config.model, reasoning_effort: config.reasoning_effort,
  scope: 'One fresh isolated full-diary call. Return subject enumeration followed by hierarchy. No baseline reruns or masks.',
  checks: ['Check Breakfast and Lunch independently in both outputs', 'Compare every enumerated subject with the final hierarchy for omissions or changes of meaning', 'Check both outputs against the source note'],
  limits: 'The new output contract can change generation. It exposes two output artifacts, not past hidden reasoning or proof of the cause of earlier omissions. One call cannot establish reliability.',
  cases: [note]
};
for (const [name, data] of [['config.json', config], ['cases.json', cases]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({calls: 1, model: config.model, effort: config.reasoning_effort, fields: Object.keys(config.output_schema.properties)}));
