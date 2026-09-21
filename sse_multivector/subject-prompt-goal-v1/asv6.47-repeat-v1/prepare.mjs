import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const read = p => JSON.parse(fs.readFileSync(path.resolve(dir, p), 'utf8'));
const config = read('../asv6.47-diverse-v1/config.json');
const diverse = read('../asv6.47-diverse-v1/cases.json');
const diary = read('../asv6.47-diagnostic-v1/cases.json');
const prompt = fs.readFileSync(diverse.prompt_path, 'utf8');
if (crypto.createHash('sha256').update(prompt).digest('hex') !== diverse.prompt_sha256)
  throw new Error('Approved prompt changed');
const notes = [...diverse.cases, diary.cases[0]];
const originals = [...config.prompts, ...read('../asv6.47-diagnostic-v1/config.json').prompts];
config.prompts = notes.flatMap(n => {
  const text = `${prompt}\n<post>\n${n.text}\n</post>`;
  if (!originals.some(p => p.text === text)) throw new Error(`Changed input: ${n.id}`);
  return [2, 3].map(trial => ({prompt_id: `${n.id}-trial-${trial}`, text}));
});
const cases = {
  ...diverse,
  scope: 'Exactly six fresh isolated Astra-low calls: trials 2 and 3 for N065, N031 and N080. Prompt, full notes and schema unchanged. No masks or older-prompt reruns.',
  baseline_directories: ['../asv6.47-diverse-v1', '../asv6.47-diagnostic-v1'],
  checks: ['Preservation of enumerated finer subjects', 'Broader-heading coverage and meaningful multiple branches', 'Source grounding and intended versus completed actions', 'Consistency across three outputs per note without assuming a canonical hierarchy'],
  limits: 'Three outputs per note identify observed variability, not corpus-wide reliability. Broad headings are not required in the initial enumeration.',
  cases: notes
};
for (const [name, data] of [['config.json', config], ['cases.json', cases]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({calls: config.prompts.map(p => p.prompt_id), model: config.model, effort: config.reasoning_effort}));
