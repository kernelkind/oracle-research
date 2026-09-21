"""Scope-only comparison against saved MPv3.11 requests and outputs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'position-selection-v4'))
spec = importlib.util.spec_from_file_location('psv4', HERE.parent / 'position-selection-v4/probe.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
pipeline = previous.pipeline


def build_config():
    prompt_dir = HERE.parent / 'mpv3.12-draft-v1'
    revision = json.loads((prompt_dir / 'mask-prompt.md.revision.json').read_text())
    original = (previous.HERE / 'mask-prompt.md').read_bytes()
    revised = (prompt_dir / 'mask-prompt.md').read_bytes()
    assert hashlib.sha256(original).hexdigest() == revision['base_sha256']
    assert hashlib.sha256(revised).hexdigest() == revision['prompt_sha256']
    expected = original.decode()
    for edit in revision['edits']:
        assert expected.count(edit['old']) == 1
        expected = expected.replace(edit['old'], edit['new'])
    assert revised.decode() == expected
    config = json.loads((previous.HERE / 'config.json').read_text())
    for job in config['prompts']:
        for edit in revision['edits']:
            assert job['text'].count(edit['old']) == 1
            job['text'] = job['text'].replace(edit['old'], edit['new'])
    assert len(config['prompts']) == 6 and config['run_directory'] == 'run'
    assert config['provider'] == 'openai-codex' and config['auth_file'] is None
    assert config['model'] == 'gpt-6-astra' and config['reasoning_effort'] == 'low'
    return config


def prepare():
    encoded = json.dumps(build_config(), ensure_ascii=False, indent=2) + '\n'
    path = HERE / 'config.json'
    if path.exists():
        assert path.read_text() == encoded, 'existing config changed'
    else:
        with path.open('x', encoding='utf-8') as output:
            output.write(encoded)
    print('Six saved requests changed only by the approved MPv3.12 scope revision.')


def run():
    prepare()
    config = pipeline.PromptRunnerConfig.load(HERE / 'config.json')
    manifest = pipeline._build_prompt_manifest(config, pipeline._runner_version(config))
    pipeline._request_history_options(config, manifest, repeat=False, history_root=HERE.parents[2])
    result = pipeline._execute_prompt_batch(config, manifest, retry_failed=False, concurrency=2)
    print(json.dumps({'completed': len(result['responses'])}))


def check():
    prepare()
    old, new = previous.records_at(previous.HERE), previous.records_at(HERE)
    valid = 0
    for case, source, subject in previous.baseline.inputs():
        print(f"\n{case['id']} | {subject}")
        old_ranges = previous.decode(old[case['id']]['final_output_raw'], source)
        print('MPv3.11:\n' + previous.baseline.position_check.highlight(source, old_ranges))
        raw = new[case['id']]['final_output_raw']
        print('MPv3.12 raw:', raw)
        try:
            ranges = previous.decode(raw, source)
        except ValueError as error:
            print(f'INVALID: {error}')
            continue
        valid += 1
        print('MPv3.12:\n' + previous.baseline.position_check.highlight(source, ranges))
        print('Fragments:', json.dumps([source[s['start']:s['end']] for s in ranges], ensure_ascii=False))
    print(f'Valid responses: {valid}/6. Semantic judgments are separate.')
    print('Usage:', json.dumps({key: sum(r['usage'][key] for r in new.values()) for key in ('input', 'output', 'cacheRead', 'cacheWrite', 'totalTokens')}, sort_keys=True))


if __name__ == '__main__':
    commands = {'prepare': prepare, 'run': run, 'check': check}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        raise SystemExit('Usage: probe.py prepare|run|check')
    commands[sys.argv[1]]()
