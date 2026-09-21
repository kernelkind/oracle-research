"""Prepare, run or inspect PSv3 using the existing runner and range decoder."""
import hashlib
import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import extraction_pipeline as pipeline

spec = importlib.util.spec_from_file_location('position_check', HERE.parent / 'position-selection-v2/check.py')
position_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(position_check)


def inputs():
    for case in json.loads((HERE / 'cases.json').read_text()):
        source = json.loads((HERE / case['source_fixture']).read_text())
        note, = [n for n in source['notes'] if n['note_id'] == case['note_id']]
        subject, = [s['subject'] for s in note['subjects'] if s[case['subject_key']] == case['subject_id']]
        yield case, note['text'], subject


def prepare(plan):
    template = (HERE / plan['prompt_file']).read_bytes()
    assert hashlib.sha256(template).hexdigest() == plan['prompt_sha256']
    old_sources = {c['source'] for c in json.loads((HERE.parent / 'position-selection-v1/cases.json').read_text())}
    config = json.loads((HERE.parent / 'position-selection-v2/config-pi.json').read_text())
    config['run_directory'] = plan['run_directory']
    config['prompts'] = []
    for case, source, subject in inputs():
        assert source not in old_sources
        assert '⟦' not in source and '⟧' not in source
        indexed = ''.join(f'[{i}]{char}' for i, char in enumerate(source)) + f'[{len(source)}]'
        text = template.decode().replace('{POST}', source).replace('{INDEXED_POST}', indexed).replace('{SUBJECT}', subject)
        assert all(s not in text for s in ('{POST}', '{INDEXED_POST}', '{SUBJECT}', '⟦', '⟧'))
        config['prompts'].append({'prompt_id': case['id'], 'text': text})
        print(f"{case['id']} | {len(source)} characters | {subject}")
    assert len(config['prompts']) == plan['calls']
    assert config['model'] == plan['model'] and config['reasoning_effort'] == plan['reasoning_effort']
    assert config['provider'] == plan['provider'] and config['auth_file'] == plan['auth_file']
    encoded = json.dumps(config, ensure_ascii=False, indent=2) + '\n'
    path = HERE / plan['config_file']
    if path.exists():
        assert path.read_bytes() == encoded.encode(), 'existing config changed'
    else:
        with path.open('x', encoding='utf-8') as output:
            output.write(encoded)


def run(plan):
    prepare(plan)
    config = pipeline.PromptRunnerConfig.load(HERE / plan['config_file'])
    manifest = pipeline._build_prompt_manifest(config, pipeline._runner_version(config))
    pipeline._request_history_options(config, manifest, repeat=False, history_root=HERE.parents[2])
    result = pipeline._execute_prompt_batch(config, manifest, retry_failed=False, concurrency=plan['concurrency'])
    print(json.dumps({'completed': len(result['responses'])}))


def check(plan):
    prepare(plan)
    config = pipeline.PromptRunnerConfig.load(HERE / plan['config_file'])
    manifest = json.loads((config.run_directory / 'manifest.json').read_text())
    records = [json.loads(line) for line in (config.run_directory / 'results.jsonl').read_text().splitlines()]
    by_id = {r['note_id']: r for r in records}
    jobs = {job.prompt_id: job for job in config.prompts}
    assert len(records) == len(by_id) and set(by_id) == set(jobs)
    valid = 0
    for case, source, subject in inputs():
        record = by_id[case['id']]
        pipeline.validate_prompt_receipt(replace(config, prompts=(jobs[case['id']],)), manifest, record)
        body = record['model_result']['request']['body']
        assert len(body['input']) == 1 and body['input'][0]['role'] == 'user'
        assert not body.get('tools') and not body.get('instructions') and not body.get('previous_response_id')
        print(f"\n{case['id']} | {subject}")
        try:
            ranges = position_check.decode(record['final_output_raw'], source)
        except ValueError as error:
            print(f'INVALID: {error}\n{record["final_output_raw"]}')
            continue
        valid += 1
        print(position_check.highlight(source, ranges))
        print('Fragments:', json.dumps([source[s['start']:s['end']] for s in ranges], ensure_ascii=False))
    print(f'\nValid range responses: {valid}/{len(records)}; semantic judgments are separate.')
    print('Usage:', json.dumps({key: sum(r['usage'][key] for r in records) for key in ('input', 'output', 'cacheRead', 'cacheWrite', 'totalTokens')}, sort_keys=True))


if __name__ == '__main__':
    commands = {'prepare': prepare, 'run': run, 'check': check}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        raise SystemExit('Usage: probe.py prepare|run|check')
    commands[sys.argv[1]](json.loads((HERE / 'plan.json').read_text()))
