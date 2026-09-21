import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const read = name => JSON.parse(fs.readFileSync(path.resolve(dir, '../asv6.44-diary-v1', name), 'utf8'));
const config = read('config.json');
const cases = read('cases.json');
const promptPath = path.resolve(dir, '../asv6.45/ASv6.45.md');
const prompt = fs.readFileSync(promptPath, 'utf8');
const hash = crypto.createHash('sha256').update(prompt).digest('hex');
if (hash !== 'c3de7a73a86377d77312af1b71624183aeca2e9cd72adf3c28754bdb467f71ec')
  throw new Error('Approved ASv6.45 changed');
config.prompts = [1, 2, 3].map(i => ({prompt_id: `N080-full-${i}`, text: `${prompt}\n<post>\n${cases.cases[0].text}\n</post>`}));
Object.assign(cases, {
  prompt_version: 'ASv6.45', prompt_path: promptPath, prompt_sha256: hash,
  baseline_directories: [...cases.baseline_directories, '../asv6.44-diary-v1'],
  interpretation: 'Compare with saved ASv6.43 and ASv6.44 full-note outputs. Accept alternative valid hierarchies. This tests the approved enumerate-before-organizing instructions, not observable internal reasoning or corpus-wide reliability.'
});
for (const [name, data] of [['config.json', config], ['cases.json', cases]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({calls: config.prompts.map(p => p.prompt_id), model: config.model, effort: config.reasoning_effort}));
