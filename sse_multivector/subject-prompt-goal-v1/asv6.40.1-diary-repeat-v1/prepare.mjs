import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const source = path.resolve(dir, '../asv6.40.1-ten-note-regression-v1');
const config = JSON.parse(fs.readFileSync(path.join(source, 'config.json'), 'utf8'));
const cases = JSON.parse(fs.readFileSync(path.join(source, 'cases.json'), 'utf8'));
const original = config.prompts.find(p => p.prompt_id === 'N080');
if (!original) throw new Error('Saved N080 prompt missing');
config.prompts = [1, 2, 3].map(i => ({prompt_id: `N080-${i}`, text: original.text}));
config.run_directory = 'run';
cases.cases = cases.cases.filter(c => c.id === 'N080');
cases.scope = 'Three intentional fresh isolated repetitions of unchanged N080 with ASv6.40.1; use --repeat. Check independent broad subject coverage, egg-laying quantity, other losses and unsupported additions against the complete note. No canonical subject list is assumed; narrower mentions do not establish separate broad-heading coverage. No baseline calls or prompt changes.';
for (const [name, data] of [['config.json', config], ['cases.json', cases]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log('Prepared three unchanged N080 prompts.');
