import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const read = p => JSON.parse(fs.readFileSync(path.resolve(dir, p), 'utf8'));
const original = read('../../mask-prompt-goal-v1/asv6.37-corpus-ten-v1/notes.json').notes;
const selections = [
  {
    id: 'N096', title: 'Spaghetti recipe', batch: '../asv6.47-seven-note-regression-v1', promptId: 'N096',
    comment: 'My assessment: useful hierarchy; no clear factual failure found. Ingredients, amounts and cooking instructions are preserved, including frying without browning and one tin of water without an invented volume. It adds ingredient and cooking-technique headings. Broader coverage is selective: Ground beef appears, but Meat does not. This is one saved output, not a reliability claim.'
  },
  {
    id: 'N029', title: 'Hashtag-only coffee post', batch: '../asv6.47-seven-note-regression-v1', promptId: 'N029',
    comment: 'My assessment: grounded but shallow. It retains the named subjects and Second coffee without inventing a literal meaning for TheRogueBatch or coffeechain. It adds no Digital currencies parent above Bitcoin or broader social-networking parent above Nostr. This illustrates the remaining selective broad-heading coverage.'
  },
  {
    id: 'N080', title: 'Diary — latest repeat (trial 3)', batch: '../asv6.47-repeat-v1', promptId: 'N080-trial-3',
    comment: 'My assessment: useful coverage across the different parts of the diary, with all 37 enumerated subjects retained. Breakfast appears independently; lunch appears under Advance lunch preparation, not a separate Lunch heading. Concern: “Four hens laying an egg a day each” chooses a per-hen interpretation; the original says “Our chickens are laying an egg a day.” It is plausible but less explicit in the source. This is the latest repeat, not the cleanest selected result.'
  }
];
const provenance = [];
const notes = selections.map(s => {
  const source = original.find(n => n.id === s.id);
  const batch = read(`${s.batch}/cases.json`);
  assert.equal(batch.cases.find(n => n.id === s.id).text, source.text);
  const outputPath = `${s.batch}/run/output.json`;
  const raw = read(outputPath).responses.find(r => r.prompt_id === s.promptId).response;
  const output = JSON.parse(raw);
  const hierarchy = output.subjects.map(e => `${'  '.repeat(e.number.split('.').length - 1)}${e.number}  ${e.subject}`).join('\n');
  const contexts = output.subjects.map(e => `${e.number}  ${e.subject}\n${e.context}`).join('\n\n');
  const enumeration = output.enumerated_subjects.map((s, i) => `${i + 1}. ${s}`).join('\n');
  for (const entry of output.subjects) assert.ok(hierarchy.includes(`${entry.number}  ${entry.subject}`));
  provenance.push({id: s.id, note_id: source.note_id, output_path: outputPath, prompt_id: s.promptId});
  return {
    id: s.id, title: s.title, text: source.text,
    results: [
      {model: 'Hierarchy', output: hierarchy, comment: s.comment},
      {model: 'Initial enumeration', output: enumeration, comment: s.comment},
      {model: 'Context explanations', output: contexts, comment: s.comment}
    ]
  };
});
const review = {schema_version: 1, title: 'ASv6.47 · Astra low · 3 saved examples', notes};
for (const [name, value] of [['review.json', review], ['sources.json', provenance]])
  fs.writeFileSync(path.join(dir, name), JSON.stringify(value, null, 2) + '\n', {flag: 'wx'});
console.log('Prepared three notes; exact generated strings, separate comments, no inference.');
