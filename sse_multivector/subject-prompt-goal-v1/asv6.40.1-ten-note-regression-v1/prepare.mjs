import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const baseline = path.resolve(dir, '../../mask-prompt-goal-v1/asv6.37-corpus-ten-v1');
const promptPath = path.resolve(dir, '../asv6.40.1/ASv6.40.1.md');
const prompt = fs.readFileSync(promptPath, 'utf8');
const notes = JSON.parse(fs.readFileSync(path.join(baseline, 'notes.json'), 'utf8')).notes
  .filter(n => !['N004', 'N038'].includes(n.id));
if (notes.length !== 8) throw new Error('Expected eight remaining original notes');
const config = JSON.parse(fs.readFileSync(path.resolve(dir, '../asv6.40.1-identifiers-v1/config.json'), 'utf8'));
config.run_directory = 'run';
config.prompts = notes.map(n => ({prompt_id: n.id, text: `${prompt}\n<post>\n${n.text}\n</post>`}));
const cases = {prompt_version: 'ASv6.40.1', prompt_path: promptPath,
  prompt_sha256: crypto.createHash('sha256').update(prompt).digest('hex'),
  baseline_directory: baseline, baseline_prompt_version: 'ASv6.37',
  scope: 'One candidate call for each of the eight remaining original ten-note cases. Compare all subjects with saved ASv6.37 outputs and complete source notes. No baseline reruns, prompt revisions or mask calls. Differences in valid wording, hierarchy, overlap and granularity are not automatically regressions.',
  model: config.model, reasoning_effort: config.reasoning_effort, cases: notes};
for (const [name, data] of [['config.json', config], ['cases.json', cases]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({prepared: notes.map(n => n.id), model: config.model, effort: config.reasoning_effort}));
