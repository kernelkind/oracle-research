import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const baseline = JSON.parse(fs.readFileSync(path.resolve(dir, '../asv6.45-diary-v1/config.json'), 'utf8')).output_schema;
const schema = {
  ...baseline,
  properties: {
    enumerated_subjects: {type: 'array', items: {type: 'string', minLength: 1}},
    ...baseline.properties
  },
  required: ['enumerated_subjects', ...baseline.required]
};
fs.writeFileSync(path.join(dir, 'output-schema.json'), JSON.stringify(schema, null, 2) + '\n', {flag: 'wx'});
console.log('Prepared ASv6.46 output schema; final hierarchy schema unchanged. No model calls.');
