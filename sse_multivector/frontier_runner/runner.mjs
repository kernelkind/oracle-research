#!/usr/bin/env node
// Frozen extraction formatting and source checks; all model transport lives in model.mjs.
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';
import { prepare as prepareModel, execute as executeModel, preview as previewModel, launchWithSelectedPi, localPiConnection } from './model.mjs';

const root = new URL('../', import.meta.url);
const sha256 = text => createHash('sha256').update(text).digest('hex');
const read = path => readFile(new URL(path, root), 'utf8');
const NIP19 = /(?<![A-Za-z0-9_])(?:nostr:)?(?:nprofile|nevent|nrelay|naddr|npub|nsec|note)1[023456789acdefghjklmnpqrstuvwxyz]{20,}(?:[?#][^\s<>"']*)?(?=$|[^A-Za-z0-9_])/gi;
const nonempty = value => typeof value === 'string' && value.trim().length > 0;

async function frozen(path, expected) {
  const text = await read(path);
  if (sha256(text) !== expected) throw new Error(`Frozen input changed: ${path}`);
  return text;
}

async function prompts() {
  const [subject, mask, schema] = await Promise.all([
    frozen('subject-prompt-goal-v1/asv6.23/ASv6.23.md', 'b80fd158b27ee0b3ddd640f10e78d7a18101f933d8758af749f6f3d2f25d506f'),
    frozen('mask-prompt-goal-v1/subject-deletion-v1/mask-prompt.md', '3bfaae265284e7b27fc0b740c7c4b214db8045d9f316f59990d5b36332d6c3e2'),
    frozen('subject-prompt-goal-v1/asv6.23/output-schema.json', 'f4fe9090fa4843397605c1a7bc163245f1cc15b71fefcef89ed31357e85f1070'),
  ]);
  return { subject, mask, schema: JSON.parse(schema) };
}

/** Render the frozen extraction inputs; auxiliary annotations never enter the prompt. */
export async function prepare(config) {
  const allowed = new Set(['provider', 'model', 'reasoning', 'stage', 'text', 'note_id', 'subject', 'max_output_tokens', 'timeout_seconds']);
  if (!config || typeof config !== 'object' || Array.isArray(config)) throw new Error('Config must be an object');
  for (const key of Object.keys(config)) if (!allowed.has(key)) throw new Error(`Unknown config field: ${key}`);
  if (!['subjects', 'masks'].includes(config.stage)) throw new Error('stage must be subjects or masks');
  if (('text' in config) === ('note_id' in config)) throw new Error('Supply exactly one of text or note_id');
  if (config.stage === 'masks' && !nonempty(config.subject)) throw new Error('masks requires one fixed subject string');
  if (config.stage === 'subjects' && 'subject' in config) throw new Error('subjects does not take a subject');
  if (config.provider === 'openai-codex' && (config.model !== 'gpt-6-astra' || config.reasoning !== 'low')) {
    throw new Error('The frozen Astra baseline requires gpt-6-astra, low');
  }
  let source;
  if ('note_id' in config) {
    const selection = JSON.parse(await read('frontier-model-comparison-v1/english-selection-v2/selection.json'));
    const matches = selection.notes.filter(note => note.id === config.note_id || note.note_id === config.note_id);
    if (matches.length !== 1) throw new Error('note_id must identify exactly one frozen selected note');
    const note = matches[0];
    source = { id: note.id, note_id: note.note_id, text: note.text };
  } else {
    source = { id: null, note_id: null, text: config.text };
  }
  if (!nonempty(source.text)) throw new Error('text must be a nonempty string');
  const p = await prompts();
  const normalized = source.text.replace(NIP19, '');
  const prompt = config.stage === 'subjects'
    ? `${p.subject}\n\n<post>\n${normalized}\n</post>`
    : p.mask.replace(/\{POST\}|\{SUBJECT\}/g, key => key === '{POST}' ? source.text : config.subject);
  const request = await prepareModel({
    provider: config.provider, model: config.model, reasoning: config.reasoning, prompt,
    ...(config.stage === 'subjects' ? { schema: p.schema } : {}),
    ...('max_output_tokens' in config ? { max_output_tokens: config.max_output_tokens } : {}),
    ...('timeout_seconds' in config ? { timeout_seconds: config.timeout_seconds } : {}),
  });
  return {
    ...request, stage: config.stage, source, subject: config.subject ?? null,
    prompt_version: config.stage === 'subjects' ? 'ASv6.23' : 'MPv3.5', schema_name: 'subjects',
    source_sha256: sha256(source.text), normalization_changed: config.stage === 'subjects' && normalized !== source.text,
  };
}

function extractionMetadata(request) {
  return {
    stage: request.stage, source_id: request.source.id, note_id: request.source.note_id,
    source_sha256: request.source_sha256, prompt_version: request.prompt_version,
  };
}

function checkOutput(request, raw, stopReason) {
  if (stopReason !== 'stop') return { valid: false, output: null, validation_error: `Generation ended with ${stopReason}` };
  let output;
  try { output = JSON.parse(raw); }
  catch { return { valid: false, output: null, validation_error: 'Output is not bare JSON' }; }
  if (request.stage === 'subjects') {
    const valid = output && !Array.isArray(output) && Object.keys(output).length === 1 &&
      Array.isArray(output.subjects) && output.subjects.every(subject => subject && !Array.isArray(subject) &&
        Object.keys(subject).length === 2 && nonempty(subject.context) && nonempty(subject.subject));
    return { valid: !!valid, output, validation_error: valid ? null : 'Output does not match the frozen subject schema' };
  }
  if (!Array.isArray(output) || output.length === 0 || !output.every(nonempty)) {
    return { valid: false, output, validation_error: 'Mask must be a nonempty array of nonempty strings' };
  }
  let end = 0;
  for (const fragment of output) {
    const start = request.source.text.indexOf(fragment, end);
    if (start === -1) return { valid: false, output, validation_error: 'Mask fragments are not exact source substrings in source order' };
    end = start + fragment.length;
  }
  return { valid: true, output, validation_error: null };
}

export async function execute(request, options) {
  const result = await executeModel(request, options);
  return { ...result, ...extractionMetadata(request), ...checkOutput(request, result.raw_text, result.stop_reason) };
}

export async function preview(request) {
  return { ...await previewModel(request), ...extractionMetadata(request), normalization_changed: request.normalization_changed };
}

const help = `Usage: run-frontier-comparison.sh preview|run [CONFIG.json] [--send]
Frozen extraction adapter. For arbitrary prompts use run-model.sh.
Reads one config from file or stdin; writes one JSON result to stdout.
Required: provider, model, reasoning, stage; exactly one of note_id or text.
Stages: subjects (ASv6.23); masks (MPv3.5, requires one fixed subject string).
Providers: openai-codex (gpt-6-astra, low), openrouter (pi-ai openai-completions models).
OpenRouter requires max_output_tokens; reasoning may be provider-default.
Optional: timeout_seconds (default 300). No retries, implicit batches, or prompt repair.
preview reads no credentials and cannot send. run requires --send.
Authentication and provider setup are shared with run-model.sh.
See run-model.sh --help for login instructions. Keep credentials outside the repository.
Before paid execution, obtain approved maximum spend.
Provider-enforced spending caps are not required.
Timeouts/output limits are not spending approval or a monetary hard cap.
Local output checks test JSON/source integrity, NOT semantic correctness.
`;

async function main() {
  const { values, positionals } = parseArgs({ allowPositionals: true, options: {
    help: { type: 'boolean' }, send: { type: 'boolean' }, 'auth-file': { type: 'string' }, 'pi-config': { type: 'boolean' },
  } });
  if (values.help) { process.stdout.write(help); return; }
  if (values['auth-file']) throw new Error('--auth-file is not supported by this frozen adapter. Authenticate with run-model.sh login and omit this option.');
  const [command, path] = positionals;
  if (!['preview', 'run'].includes(command) || positionals.length > 2) throw new Error(help);
  if (command === 'run' && !values.send) throw new Error('Sending requires the explicit --send flag');
  if (command === 'preview' && values.send) throw new Error('preview does not accept --send');
  const input = path ? await readFile(path, 'utf8') : await new Response(process.stdin).text();
  const request = await prepare(JSON.parse(input));
  if (command === 'preview') { process.stdout.write(JSON.stringify(await preview(request), null, 2) + '\n'); return; }
  if (!values['pi-config']) return launchWithSelectedPi(input);
  const connection = await localPiConnection(request.model.provider);
  request.model = { ...request.model, baseUrl: connection.baseUrl };
  const result = await execute(request, { apiKey: connection.apiKey });
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
  if (!result.valid) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(error => { process.stderr.write(`${error.message}\n`); process.exitCode = 1; });
}
