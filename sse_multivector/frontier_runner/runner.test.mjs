import assert from 'node:assert/strict';
import { readFile, mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';
import { prepare, preview, execute } from './runner.mjs';

test('comparison CLI help preserves spending approval without requiring provider caps', () => {
  const result = spawnSync(process.execPath, [new URL('runner.mjs', import.meta.url).pathname, '--help'],
    { encoding: 'utf8', env: {} });
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /approved maximum spend/);
  assert.match(result.stdout, /Authentication and provider setup are shared with run-model\.sh/);
  assert.match(result.stdout, /Provider-enforced spending caps are not required/);
});

const root = new URL('../', import.meta.url);
const post = 'I bake bread. nostr:npub1' + 'q'.repeat(30) + '\nhttps://example.com/\n';
const subjectPrompt = await readFile(new URL('subject-prompt-goal-v1/asv6.23/ASv6.23.md', root), 'utf8');
const maskPrompt = await readFile(new URL('mask-prompt-goal-v1/subject-deletion-v1/mask-prompt.md', root), 'utf8');
const schema = JSON.parse(await readFile(new URL('subject-prompt-goal-v1/asv6.23/output-schema.json', root), 'utf8'));
const astra = { provider: 'openai-codex', model: 'gpt-6-astra', reasoning: 'low' };
const muse = { provider: 'openrouter', model: 'meta/muse-spark-1.3-contributor', reasoning: 'low', max_output_tokens: 4096 };
const config = (route = astra, extra = {}) => ({ ...route, stage: 'subjects', text: post, ...extra });

test('subject rendering retains the frozen schema, normalization, and prompt bytes', async () => {
  const request = await prepare(config());
  assert.equal(request.prompt, subjectPrompt + '\n\n<post>\nI bake bread. \nhttps://example.com/\n\n</post>');
  assert.deepEqual(request.schema, schema);
  assert.equal(request.prompt_version, 'ASv6.23');
});

test('mask rendering keeps the original post and passes exactly one fixed subject', async () => {
  const subject = 'Bread baking';
  const request = await prepare(config(astra, { stage: 'masks', subject }));
  assert.equal(request.prompt, maskPrompt.replace('{POST}', post).replace('{SUBJECT}', subject));
  assert.equal(request.schema, null); // Frozen MPv3.5 used bare-array text, not an object envelope.
  await assert.rejects(prepare(config(astra, { stage: 'masks' })), /subject/);
  await assert.rejects(prepare(config(astra, { stage: 'masks', subject: { context: 'x', subject } })), /subject/);
});

test('676 selected inputs match the existing frozen production formatter', async () => {
  const file = new URL('frontier-model-comparison-v1/english-selection-v2/selection.json', root);
  const notes = JSON.parse(await readFile(file, 'utf8')).notes;
  const python = spawnSync('python3', ['-B', '-c',
    'import importlib.util,sys,json,pathlib; p=pathlib.Path(sys.argv[1]); s=importlib.util.spec_from_file_location("extraction_pipeline",p/"extraction_pipeline.py"); m=importlib.util.module_from_spec(s); sys.modules[s.name]=m; s.loader.exec_module(m); notes=json.loads(pathlib.Path(sys.argv[2]).read_text())["notes"]; print(json.dumps([m._takeaway_input(n["text"]) for n in notes]))',
    root.pathname, file.pathname], { encoding: 'utf8', maxBuffer: 4 * 1024 * 1024 });
  assert.equal(python.status, 0, python.stderr);
  const normalized = JSON.parse(python.stdout);
  assert.equal(notes.length, 676);
  let changed = 0;
  for (let i = 0; i < notes.length; i++) {
    const r = await prepare({ ...astra, stage: 'subjects', note_id: notes[i].id });
    assert.equal(r.prompt, subjectPrompt + '\n\n<post>\n' + normalized[i] + '\n</post>');
    if (notes[i].text !== normalized[i]) changed++;
  }
  assert.equal(changed, 74);
});

for (const route of [astra, muse,
  { ...muse, model: 'deepseek/deepseek-v4.1-flash' },
  { ...muse, model: 'xiaomi/mimo-v2.6-pro' },
  { ...muse, model: 'z-ai/glm-5.3-flash' }]) {
  test(`${route.model}: actual pi-ai payload has one user message, no added instructions/history/tools`, async () => {
    const out = await preview(await prepare(config(route)));
    assert.equal(out.network_requests, 0);
    assert.equal(out.credentials_read, false);
    assert.equal(out.body.model, route.model);
    const messages = out.body.input ?? out.body.messages;
    assert.equal(messages.length, 1);
    assert.equal(messages[0].role, 'user');
    const content = typeof messages[0].content === 'string' ? messages[0].content : messages[0].content[0].text;
    assert.equal(content, out.prompt);
    assert.equal(out.body.instructions ?? '', '');
    assert.ok(!out.body.tools);
    assert.ok(!out.body.previous_response_id);
    assert.ok(!JSON.stringify(out.body).includes('helpful assistant'));
    assert.deepEqual((out.body.text?.format ?? out.body.response_format?.json_schema).schema, schema);
    assert.equal(out.body.reasoning.effort, 'low');
    assert.ok(out.headers.authorization.includes('REDACTED'));
    if (route.provider === 'openrouter') {
      assert.deepEqual(out.body.provider, { require_parameters: true, allow_fallbacks: true });
      assert.equal(out.body.max_tokens, 4096);
    } else {
      assert.equal(out.url, 'https://chatgpt.com/backend-api/codex/responses');
      assert.equal(out.body.store, false);
    }
  });
}

test('preview sends MPv3.5 without adding a subject schema or context from other calls', async () => {
  for (const route of [astra, muse]) {
    const r = await preview(await prepare(config(route, { stage: 'masks', subject: 'Bread baking' })));
    assert.ok(!r.body.response_format);
    assert.ok(!r.body.text?.format);
    assert.ok(r.prompt.includes(post));
    assert.ok(!r.prompt.includes('auxiliary secret context'));
  }
});

for (const stage of ['subjects', 'masks']) {
  test(`Astra ${stage}: omit verbosity and summaries, retain low effort and frozen output format`, async () => {
    const request = await prepare(config(astra, {
      stage, ...(stage === 'masks' ? { subject: 'Bread baking' } : {}),
    }));
    const out = await preview(request);
    assert.deepEqual({ text: out.body.text, reasoning: out.body.reasoning }, {
      text: stage === 'subjects'
        ? { format: { type: 'json_schema', name: 'subjects', strict: true, schema } }
        : undefined,
      reasoning: { effort: 'low' },
    });
    assert.equal(out.body.input[0].content[0].text, request.prompt);
  });
}

test('provider default reasoning does not silently become off; unsupported efforts fail', async () => {
  const r = await preview(await prepare(config({ ...muse, reasoning: 'provider-default' })));
  assert.ok(!r.body.reasoning);
  await assert.rejects(prepare(config({ ...muse, model: 'z-ai/glm-5.3-flash', reasoning: 'medium' })), /reasoning/);
  await assert.rejects(prepare(config({ ...astra, reasoning: 'medium' })), /low/);
  await assert.rejects(prepare(config({ ...astra, max_output_tokens: 4096 })), /output.*limit|output.*cap/);
});

test('unknown options, conflicting sources and wrong routes fail before transport', async () => {
  for (const extra of [{ tools: [] }, { system: 'secret' }, { note_id: 'E0002' }, { subject: 'wrong stage' }]) {
    await assert.rejects(prepare(config(astra, extra)));
  }
  await assert.rejects(prepare(config({ ...astra, provider: 'openai' })));
  await assert.rejects(prepare({ ...astra, stage: 'subjects', note_id: 'nonexistent' }));
});

const sse = (frames) => new Response(frames.map(x => `data: ${typeof x === 'string' ? x : JSON.stringify(x)}\n\n`).join(''),
  { headers: { 'content-type': 'text/event-stream' } });
function openRouterReply(text) {
  return sse([
    { id: 'test-response', model: muse.model, provider: 'test-provider', choices: [{ index: 0, delta: { role: 'assistant', content: text }, finish_reason: null }] },
    { id: 'test-response', choices: [{ index: 0, delta: {}, finish_reason: 'stop' }], usage: { prompt_tokens: 100, completion_tokens: 20, prompt_tokens_details: { cached_tokens: 40 }, completion_tokens_details: { reasoning_tokens: 5 } } },
    '[DONE]',
  ]);
}

test('execution uses the same payload and preserves raw output and cache accounting', async () => {
  const request = await prepare(config(muse));
  const expected = await preview(request);
  let calls = 0;
  const result = await execute(request, { apiKey: 'test-only', fetch: async (url, options) => {
    calls++;
    assert.deepEqual(JSON.parse(options.body), expected.body);
    return openRouterReply('{"subjects":[{"context":"Bread","subject":"Bread baking"}]}');
  } });
  assert.equal(calls, 1);
  assert.equal(result.valid, true);
  assert.equal(result.output.subjects[0].subject, 'Bread baking');
  assert.equal(result.usage.input, 60); // pi-ai input excludes cacheRead, unlike the old Codex totals.
  assert.equal(result.usage.cacheRead, 40);
  assert.equal(result.usage.output, 20); // Includes reasoning: do not add reasoning again.
});

test('invalid structured output and masks are retained, not repaired or retried', async () => {
  for (const [extra, text] of [
    [{}, '{"subjects":["old schema"]}'],
    [{}, '```json\n{"subjects":[]}\n```'],
    [{ stage: 'masks', subject: 'Bread baking' }, '["not in source"]'],
    [{ stage: 'masks', subject: 'Bread baking' }, '["bread", "bake"]'],
    [{ stage: 'masks', subject: 'Bread baking' }, '[]'],
  ]) {
    let calls = 0;
    const result = await execute(await prepare(config(muse, extra)), { apiKey: 'test-only', fetch: async () => {
      calls++; return openRouterReply(text);
    } });
    assert.equal(calls, 1);
    assert.equal(result.valid, false);
    assert.equal(result.raw_text, text);
  }
});

test('upstream errors are recorded once, not silently retried', async () => {
  let calls = 0;
  const result = await execute(await prepare(config(muse)), { apiKey: 'test-only', fetch: async () => {
    calls++;
    return new Response('{"error":{"message":"test failure"}}', { status: 429 });
  } });
  assert.equal(calls, 1);
  assert.equal(result.valid, false);
  assert.equal(result.stop_reason, 'error');
});

test('subscription execution decodes the real SSE format and retains uncached/cached totals', async () => {
  const text = '["bake bread"]';
  const item = { id: 'msg-test', type: 'message', role: 'assistant', status: 'completed',
    content: [{ type: 'output_text', text, annotations: [] }] };
  const response = { id: 'resp-test', model: 'gpt-6-astra', status: 'completed', output: [item],
    usage: { input_tokens: 100, output_tokens: 20, input_tokens_details: { cached_tokens: 40 }, output_tokens_details: { reasoning_tokens: 5 } } };
  const token = 'test.' + Buffer.from(JSON.stringify({ 'https://api.openai.com/auth': { chatgpt_account_id: 'test-account' } })).toString('base64') + '.signature';
  let calls = 0;
  const result = await execute(await prepare(config(astra, { stage: 'masks', subject: 'Bread baking' })), {
    apiKey: token,
    fetch: async () => {
      calls++;
      return sse([
        { type: 'response.created', response: { id: 'resp-test', status: 'in_progress' } },
        { type: 'response.output_item.added', output_index: 0, item: { ...item, content: [] } },
        { type: 'response.output_text.delta', output_index: 0, content_index: 0, delta: text },
        { type: 'response.output_item.done', output_index: 0, item },
        { type: 'response.completed', response },
      ]);
    },
  });
  assert.equal(calls, 1);
  assert.equal(result.valid, true, result.error);
  assert.deepEqual(result.output, ['bake bread']);
  assert.equal(result.usage.input, 60);
  assert.equal(result.usage.cacheRead, 40);
  assert.equal(result.usage.output, 20);
  assert.equal(result.response_metadata.usage.output_tokens_details.reasoning_tokens, 5);
  assert.ok(!JSON.stringify(result).includes(token));
  assert.ok(!JSON.stringify(result).includes('test-account'));
});

test('placeholder-looking source text is never interpolated as an instruction', async () => {
  const text = 'A literal {SUBJECT} and {POST} are in this post.';
  const r = await prepare(config(astra, { text, stage: 'masks', subject: 'Placeholder syntax' }));
  assert.ok(r.prompt.includes(`<post>\n${text}\n</post>`));
  assert.ok(r.prompt.includes('<subject>\nPlaceholder syntax\n</subject>'));
});

test('completed independent calls do not supply history to the next call', async () => {
  await execute(await prepare(config(muse, { text: 'previous post marker' })), {
    apiKey: 'test-only', fetch: async () => openRouterReply('{"subjects":[]}'),
  });
  const next = await preview(await prepare(config(muse, { text: 'next post marker' })));
  assert.equal(next.body.messages.length, 1);
  assert.ok(!JSON.stringify(next.body).includes('previous post marker'));
});

test('truncation and transport timeouts remain failures even when text parses as JSON', async () => {
  const r = await execute(await prepare(config(muse)), { apiKey: 'test-only', fetch: async () => sse([
    { choices: [{ index: 0, delta: { content: '{"subjects":[]}' }, finish_reason: 'length' }] }, '[DONE]',
  ]) });
  assert.equal(r.valid, false);
  assert.equal(r.raw_text, '{"subjects":[]}');
  const controller = new AbortController();
  controller.abort();
  let sent = 0;
  const aborted = await execute(await prepare(config(muse)), { apiKey: 'test-only', signal: controller.signal,
    fetch: async () => { sent++; return openRouterReply('{"subjects":[]}'); } });
  assert.equal(aborted.valid, false);
  assert.equal(sent, 0);
});

test('CLI preview works without credentials and run requires explicit sending', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'frontier-runner-test-'));
  try {
    const env = { PATH: process.env.PATH, HOME: dir };
    const cli = new URL('runner.mjs', import.meta.url).pathname;
    const result = spawnSync(process.execPath, [cli, 'preview'], { input: JSON.stringify(config()), encoding: 'utf8', env });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(JSON.parse(result.stdout).network_requests, 0);
    const denied = spawnSync(process.execPath, [cli, 'run'], { input: JSON.stringify(config()), encoding: 'utf8', env });
    assert.notEqual(denied.status, 0);
    assert.match(denied.stderr, /--send/);
    await writeFile(join(dir, 'fake-auth.json'), '{"OPENAI_API_KEY":"must-not-use"}');
    const wrongAuth = spawnSync(process.execPath, [cli, 'run', '--send', '--auth-file', join(dir, 'fake-auth.json')],
      { input: JSON.stringify(config()), encoding: 'utf8', env });
    assert.notEqual(wrongAuth.status, 0);
    assert.ok(!wrongAuth.stderr.includes('must-not-use'));
  } finally { await rm(dir, { recursive: true }); }
});

test('a timed-out HTTP attempt is cancelled and not retried', async () => {
  let calls = 0;
  const result = await execute(await prepare(config(muse, { timeout_seconds: 1 })), {
    apiKey: 'test-only', fetch: async (_url, options) => {
      calls++;
      await new Promise((resolve, reject) => {
        const timer = setTimeout(resolve, 5000);
        options.signal.addEventListener('abort', () => { clearTimeout(timer); reject(options.signal.reason); }, { once: true });
      });
      throw new Error('The request should have been cancelled');
    },
  });
  assert.equal(calls, 1);
  assert.equal(result.valid, false);
  assert.ok(['aborted', 'error'].includes(result.stop_reason));
});

test('actual OpenRouter provider and raw reasoning usage survive SDK normalization', async () => {
  const result = await execute(await prepare(config(muse)), {
    apiKey: 'test-only', fetch: async () => openRouterReply('{"subjects":[]}'),
  });
  assert.equal(result.response_metadata.provider, 'test-provider');
  assert.equal(result.response_metadata.model, muse.model);
  assert.equal(result.response_metadata.usage.completion_tokens_details.reasoning_tokens, 5);
});
