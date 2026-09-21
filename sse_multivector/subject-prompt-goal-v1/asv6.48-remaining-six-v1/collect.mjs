import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const read = p => JSON.parse(fs.readFileSync(path.resolve(dir, p), 'utf8'));
const notePath = '../../mask-prompt-goal-v1/asv6.37-corpus-ten-v1/notes.json';
const notes = read(notePath).notes;
const cases = read('cases.json');
const sources = [];
const responses = notes.map(note => {
  const batch = ['N096', 'N029', 'N080'].includes(note.id) ? '../asv6.48-probe-v1'
    : note.id === 'N065' ? '../asv6.48-coffee-repeat-v1' : '.';
  const promptId = note.id === 'N065' ? 'N065-trial-1' : note.id;
  const origin = read(`${batch}/cases.json`);
  assert.equal(origin.prompt_sha256, cases.prompt_sha256);
  assert.equal(origin.cases.find(n => n.id === note.id).text, note.text);
  const saved = read(`${batch}/run/output.json`).responses.find(r => r.prompt_id === promptId);
  assert.ok(saved, `Missing ${note.id}`);
  const parsed = JSON.parse(saved.response);
  assert.deepEqual(Object.keys(parsed), ['subjects']);
  assert.ok(parsed.subjects.length > 0);
  sources.push({id: note.id, note_id: note.note_id, output_path: `${batch}/run/output.json`, prompt_id: promptId, subjects: parsed.subjects.length});
  return {prompt_id: note.id, response: saved.response};
});
assert.equal(responses.length, 10);
assert.equal(new Set(responses.map(r => r.prompt_id)).size, 10);
const manifest = {
  schema_version: 1, prompt_version: 'ASv6.48', prompt_sha256: cases.prompt_sha256,
  notes_path: notePath, sources,
  selection: 'One unchanged response per original note, in original note order. N065 uses the first trial, not a quality-selected repeat. All original receipts and additional trials remain preserved.'
};
for (const [name, data] of [['ten-note-output.json', {schema_version: 1, responses}], ['ten-note-sources.json', manifest]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({notes: responses.length, subjects: sources.reduce((n, s) => n + s.subjects, 0), sources}));
