import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const baseline = path.resolve(dir, '../asv6.43-probe-v1');
const prior = JSON.parse(fs.readFileSync(path.join(baseline, 'cases.json'), 'utf8'));
const original = prior.cases.find(n => n.id === 'N080');
const paragraphs = original.text.split('\n\n').filter(p => p.startsWith('Our chickens are laying'));
if (paragraphs.length !== 1) throw new Error('Expected exactly one egg-and-meals paragraph');
const text = paragraphs[0];
const prompt = fs.readFileSync(prior.prompt_path, 'utf8');
const hash = crypto.createHash('sha256').update(prompt).digest('hex');
if (hash !== prior.prompt_sha256) throw new Error('ASv6.43 changed since full-note run');
const config = JSON.parse(fs.readFileSync(path.join(baseline, 'config.json'), 'utf8'));
config.run_directory = 'run';
config.prompts = [{prompt_id: 'N080-paragraph', text: `${prompt}\n<post>\n${text}\n</post>`}];
const cases = {
  prompt_version: 'ASv6.43', prompt_sha256: hash,
  model: config.model, reasoning_effort: config.reasoning_effort,
  saved_full_note_run: baseline,
  change: 'Replace the full N080 diary with its unchanged egg-and-meals paragraph. Instructions, examples, schema, model and effort remain unchanged. One fresh isolated call; no baseline rerun.',
  question: 'Do independent Breakfast and Lunch headings appear when this passage is presented without the rest of the diary, while its specific subjects remain?',
  interpretation_limits: 'One output per condition is preliminary. Removing the rest of the note changes both task size and available context; an improvement would not identify which of these caused it. A continued omission would show that full-note crowding is not necessary for that omission.',
  cases: [{id: 'N080-paragraph', source_note_id: original.note_id, text}]
};
for (const [name, data] of [['config.json', config], ['cases.json', cases]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({model: config.model, effort: config.reasoning_effort, text}));
