import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const source = path.resolve(dir, '../asv6.40.1-identifiers-v1');
const config = JSON.parse(fs.readFileSync(path.join(source, 'config.json'), 'utf8'));
const cases = JSON.parse(fs.readFileSync(path.join(source, 'cases.json'), 'utf8'));
const original = config.prompts.find(p => p.prompt_id === 'R02');
if (!original) throw new Error('Saved R02 prompt missing');
config.prompts = [1, 2, 3].map(i => ({prompt_id: `R02-${i}`, text: original.text}));
config.run_directory = 'run';
cases.cases = cases.cases.filter(c => c.id === 'R02');
cases.scope = 'Three intentional fresh isolated repetitions of unchanged saved R02 with ASv6.40.1; run with --repeat. Assess hashtag/name retention and other semantic errors. No baseline calls or prompt revisions.';
for (const [name, data] of [['config.json', config], ['cases.json', cases]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log('Prepared three identical prompts with distinct trial IDs.');
