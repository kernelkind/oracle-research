import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const read = p => JSON.parse(fs.readFileSync(path.resolve(dir, p), 'utf8'));
const config = read('../asv6.47-diagnostic-v1/config.json');
const prior = read('../asv6.47-diagnostic-v1/cases.json');
const prompt = fs.readFileSync(prior.prompt_path, 'utf8');
if (crypto.createHash('sha256').update(prompt).digest('hex') !== prior.prompt_sha256)
  throw new Error('ASv6.47 changed');
const source = read('../../mask-prompt-goal-v1/asv6.37-corpus-ten-v1/notes.json').notes;
const notes = ['N065', 'N031'].map(id => {
  const note = source.find(n => n.id === id);
  if (!note) throw new Error(`Missing ${id}`);
  return note;
});
config.prompts = notes.map(n => ({prompt_id: n.id, text: `${prompt}\n<post>\n${n.text}\n</post>`}));
const cases = {
  prompt_version: 'ASv6.47', prompt_path: prior.prompt_path, prompt_sha256: prior.prompt_sha256,
  model: config.model, reasoning_effort: config.reasoning_effort,
  scope: 'Two fresh isolated calls, one per multipart note. Unchanged prompt and settings. No baseline reruns, masks or new examples.',
  baseline_directories: ['../asv6.40.1-ten-note-regression-v1', '../asv6.43-probe-v1', '../../mask-prompt-goal-v1/asv6.37-corpus-ten-v1'],
  selection: 'N065 combines coffee shops, technology restrictions, contemplated retaliation, actual customer behavior and rhetoric. N031 combines supermarket-food criticism, growing food, an allotment, and a breakfast preference. Both have saved outputs.',
  checks: ['Enumerate fine subjects without requiring abstract headings in the initial list', 'Preserve fine subjects when forming broader headings and multiple meaningful branches', 'Examine general-subject coverage without demanding one canonical hierarchy', 'Check source grounding, references, rhetoric, and intended versus completed actions'],
  limits: 'One output per note is a qualitative probe, not a reliable success rate. Saved older prompts differ in more than one instruction and do not establish causal attribution.',
  cases: notes
};
for (const [name, data] of [['config.json', config], ['cases.json', cases]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({calls: notes.map(n => n.id), model: config.model, effort: config.reasoning_effort}));
