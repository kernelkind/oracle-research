import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const oldDir = path.resolve(dir, '../asv6.39-simplification-v1');
const promptPath = path.resolve(dir, '../asv6.40.1/ASv6.40.1.md');
const prompt = fs.readFileSync(promptPath, 'utf8');
const previous = JSON.parse(fs.readFileSync(path.join(oldDir, 'cases.json'), 'utf8'));
const cases = previous.cases.filter(c => ['R01', 'R02'].includes(c.id))
  .map(({id, text, note_id}) => ({id, text, note_id, origin: 'unchanged saved real note'}));
const pubkey = 'nostr:npub1' + 'q'.repeat(58);
const event = 'nostr:nevent1' + 'p'.repeat(70);
cases.push({id: 'S01', origin: 'synthetic; patterned identifiers, not functional keys',
  text: `I repaired the broken hinge on my greenhouse door today.\n\nhttps://example.org/bitcoin-mining-guide\n${pubkey}\n${event}\n9e107d9d372bb6826bd81d3542a419d69e107d9d372bb6826bd81d3542a419d6\n550e8400-e29b-41d4-a716-446655440000`});
cases.push({id: 'S02', origin: 'synthetic; patterned identifier, not a functional key',
  text: `A Nostr public key identifies an account; a private key is used to sign events. I share my public key, not my private key. ${pubkey}\nI also publish a cryptographic hash so people can check that the downloaded file is unchanged.\n9e107d9d372bb6826bd81d3542a419d69e107d9d372bb6826bd81d3542a419d6`});
const config = JSON.parse(fs.readFileSync(path.join(oldDir, 'config.json'), 'utf8'));
config.auth_file = null;
config.run_directory = 'run';
config.prompts = cases.map(c => ({prompt_id: c.id, text: `${prompt}\n<post>\n${c.text}\n</post>`}));
const record = {prompt_version: 'ASv6.40.1', prompt_path: promptPath,
  prompt_sha256: crypto.createHash('sha256').update(prompt).digest('hex'),
  scope: 'Four fresh isolated calls, one per note. No baseline reruns. Inspect named subjects and hashtags, exclusion of opaque strings/URL contents, and preservation of prose discussing identifiers. Do not require a canonical heading list.',
  model: config.model, reasoning_effort: config.reasoning_effort, cases};
for (const [name, data] of [['cases.json', record], ['config.json', config]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({prepared: cases.map(c => c.id), model: config.model, effort: config.reasoning_effort}));
