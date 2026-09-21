import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const baseline = path.resolve(dir, '../../mask-prompt-goal-v1/asv6.37-corpus-ten-v1');
const promptPath = path.resolve(dir, '../asv6.43/ASv6.43.md');
const prompt = fs.readFileSync(promptPath, 'utf8');
const source = JSON.parse(fs.readFileSync(path.join(baseline, 'notes.json'), 'utf8')).notes;
const notes = ['N080', 'N065', 'N004'].map(id => {
  const note = source.find(n => n.id === id);
  if (!note) throw new Error(`Missing ${id}`);
  return note;
});
const config = JSON.parse(fs.readFileSync(path.resolve(dir, '../asv6.40.1-identifiers-v1/config.json'), 'utf8'));
config.run_directory = 'run';
config.prompts = notes.map(n => ({prompt_id: n.id, text: `${prompt}\n<post>\n${n.text}\n</post>`}));
const cases = {
  prompt_version: 'ASv6.43', prompt_path: promptPath,
  prompt_sha256: crypto.createHash('sha256').update(prompt).digest('hex'),
  model: config.model, reasoning_effort: config.reasoning_effort,
  scope: 'Three isolated candidate calls, no baseline calls or masks. Compare with saved ASv6.40.1 and ASv6.37 outputs. Check general-heading coverage alongside specific-subject preservation and unsupported additions; accept alternative valid hierarchy arrangements. This tests the whole revision, not construction order in isolation.',
  checks: {
    N080: 'Broad breakfast/lunch coverage without dropping particulars; audit all output against the diary. Record egg quantity separately, not as a promised fix.',
    N065: 'Coffee shops and device subjects alongside policy, response, and rhetorical meanings; preserve contemplated versus actual actions.',
    N004: 'Coffee shops and rave subjects; retain unresolved coffeechain without inventing a commercial coffee chain or a subject from the video URL.'
  },
  saved_baselines: ['../asv6.40.1-ten-note-regression-v1', '../asv6.40.1-diary-repeat-v1', '../asv6.40.1-identifiers-v1', baseline],
  cases: notes
};
for (const [name, data] of [['config.json', config], ['cases.json', cases]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({prepared: notes.map(n => n.id), model: config.model, effort: config.reasoning_effort}));
