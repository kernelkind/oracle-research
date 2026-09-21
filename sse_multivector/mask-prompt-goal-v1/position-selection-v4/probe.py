"""PSv4: word-position variant on the unchanged PSv3 inputs and saved baseline."""
import hashlib
import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path

from selection import decode, index_post

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('psv3', HERE.parent / 'position-selection-v3/probe.py')
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
pipeline = baseline.pipeline


def prepare():
    template = (HERE / 'mask-prompt.md').read_bytes()
    original = (HERE.parent / 'position-selection-v2/mask-prompt.md').read_text()
    edits = json.loads((HERE / 'prompt-edits.json').read_text())
    assert hashlib.sha256(original.encode()).hexdigest() == edits['base_sha256']
    assert template.decode() == original.replace(edits['edits'][0]['old'], edits['edits'][0]['new'])
    config = json.loads((baseline.HERE / 'config.json').read_text())
    config['run_directory'] = 'run'
    config['prompts'] = []
    old_config = json.loads((baseline.HERE / 'config.json').read_text())
    for case, source, subject in baseline.inputs():
        indexed = index_post(source)
        replacements = {'{POST}': source, '{INDEXED_POST}': indexed, '{SUBJECT}': subject}
        text = template.decode()
        for key, value in replacements.items():
            text = text.replace(key, value)
        old_job, = [p for p in old_config['prompts'] if p['prompt_id'] == case['id']]
        assert f'<post>\n{source}\n</post>' in old_job['text']
        assert f'<subject>\n{subject}\n</subject>' in old_job['text']
        config['prompts'].append({'prompt_id': case['id'], 'text': text})
    assert len(config['prompts']) == 6
    assert config['model'] == 'gpt-6-astra' and config['reasoning_effort'] == 'low'
    assert config['provider'] == 'openai-codex' and config['auth_file'] is None
    encoded = json.dumps(config, ensure_ascii=False, indent=2) + '\n'
    path = HERE / 'config.json'
    if path.exists():
        assert path.read_text() == encoded, 'existing config changed'
    else:
        with path.open('x', encoding='utf-8') as output:
            output.write(encoded)
    print('Six unchanged note/subject pairs; only output instructions and indexed copies changed.')


def run():
    prepare()
    config = pipeline.PromptRunnerConfig.load(HERE / 'config.json')
    manifest = pipeline._build_prompt_manifest(config, pipeline._runner_version(config))
    pipeline._request_history_options(config, manifest, repeat=False, history_root=HERE.parents[2])
    result = pipeline._execute_prompt_batch(config, manifest, retry_failed=False, concurrency=2)
    print(json.dumps({'completed': len(result['responses'])}))


def records_at(directory):
    config = pipeline.PromptRunnerConfig.load(directory / 'config.json')
    manifest = json.loads((config.run_directory / 'manifest.json').read_text())
    records = [json.loads(line) for line in (config.run_directory / 'results.jsonl').read_text().splitlines()]
    by_id = {r['note_id']: r for r in records}
    assert len(records) == len(by_id) == len(config.prompts)
    for job in config.prompts:
        record = by_id[job.prompt_id]
        pipeline.validate_prompt_receipt(replace(config, prompts=(job,)), manifest, record)
        body = record['model_result']['request']['body']
        assert len(body['input']) == 1 and body['input'][0]['role'] == 'user'
        assert not body.get('tools') and not body.get('instructions') and not body.get('previous_response_id')
    return by_id


def check():
    prepare()
    current, previous = records_at(HERE), records_at(baseline.HERE)
    valid = 0
    for case, source, subject in baseline.inputs():
        print(f"\n{case['id']} | {subject}")
        old_ranges = baseline.position_check.decode(previous[case['id']]['final_output_raw'], source)
        print('MPv3.10 (saved):\n' + baseline.position_check.highlight(source, old_ranges))
        raw = current[case['id']]['final_output_raw']
        print('MPv3.11 raw:', raw)
        try:
            ranges = decode(raw, source)
        except ValueError as error:
            print(f'INVALID: {error}')
            continue
        valid += 1
        print('MPv3.11:\n' + baseline.position_check.highlight(source, ranges))
        print('Fragments:', json.dumps([source[s['start']:s['end']] for s in ranges], ensure_ascii=False))
    print(f'Valid responses: {valid}/6; semantic judgments are separate.')
    for name, records in [('PSv3', previous), ('PSv4', current)]:
        print(name, 'usage:', json.dumps({key: sum(r['usage'][key] for r in records.values()) for key in ('input', 'output', 'cacheRead', 'cacheWrite', 'totalTokens')}, sort_keys=True))


if __name__ == '__main__':
    commands = {'prepare': prepare, 'run': run, 'check': check}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        raise SystemExit('Usage: probe.py prepare|run|check')
    commands[sys.argv[1]]()
