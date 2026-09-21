"""Small occurrence-selection probe reusing MPv3.11 and its existing decoder."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'position-selection-v4'))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


previous = load_module('psv4', HERE.parent / 'position-selection-v4/probe.py')
inline = load_module('inline_probe', HERE.parent / 'inline-format-v1/probe.py')
pipeline = previous.pipeline


def load_cases():
    return json.loads((HERE / 'cases.json').read_text())


def positions(ranges):
    return {i for span in ranges for i in range(span['start'], span['end'])}


def expectations(case):
    marked = case['required_marked_note']
    source = marked.replace('⟦', '').replace('⟧', '')
    required = inline.parse_inline(source, marked)
    forbidden = inline.parse_inline(source, case['excluded_marked_note'])
    if positions(required) & positions(forbidden):
        raise ValueError('required and excluded locations overlap')
    return source, required, forbidden


def build_config(cases):
    plan = json.loads((HERE / 'plan.json').read_text())
    template = (HERE / plan['prompt_file']).read_bytes()
    assert hashlib.sha256(template).hexdigest() == plan['prompt_sha256']
    config = json.loads((previous.HERE / 'config.json').read_text())
    config['prompts'] = []
    config['run_directory'] = 'run'
    for case in cases:
        source, _, _ = expectations(case)
        text = template.decode().replace('{POST}', source).replace('{INDEXED_POST}', previous.index_post(source)).replace('{SUBJECT}', case['subject'])
        config['prompts'].append({'prompt_id': case['id'], 'text': text})
    assert len(cases) == len({c['id'] for c in cases}) == plan['calls']
    for field in ('model', 'reasoning_effort', 'provider', 'auth_file'):
        assert config[field] == plan[field]
    return config


def prepare():
    cases = load_cases()
    encoded = json.dumps(build_config(cases), ensure_ascii=False, indent=2) + '\n'
    path = HERE / 'config.json'
    if path.exists():
        assert path.read_text() == encoded, 'existing config changed'
    else:
        with path.open('x', encoding='utf-8') as output:
            output.write(encoded)
    for case in cases:
        source, required, forbidden = expectations(case)
        print(f"{case['id']} | {case['subject']}\nRequired: {previous.baseline.position_check.highlight(source, required)}\nExclude: {previous.baseline.position_check.highlight(source, forbidden)}")


def run():
    prepare()
    config = pipeline.PromptRunnerConfig.load(HERE / 'config.json')
    manifest = pipeline._build_prompt_manifest(config, pipeline._runner_version(config))
    pipeline._request_history_options(config, manifest, repeat=False, history_root=HERE.parents[2])
    result = pipeline._execute_prompt_batch(config, manifest, retry_failed=False, concurrency=2)
    print(json.dumps({'completed': len(result['responses'])}))


def check():
    records = previous.records_at(HERE)
    valid, target_checks = 0, 0
    for case in load_cases():
        source, required, forbidden = expectations(case)
        raw = records[case['id']]['final_output_raw']
        print(f"\n{case['id']} | {case['subject']}\nRaw: {raw}")
        try:
            ranges = previous.decode(raw, source)
        except ValueError as error:
            print(f'INVALID: {error}')
            continue
        valid += 1
        selected = positions(ranges)
        covered = positions(required) <= selected
        excluded = not (positions(forbidden) & selected)
        target_checks += covered and excluded
        print(previous.baseline.position_check.highlight(source, ranges))
        print(f'Required occurrences covered: {covered}; wrong-sense occurrences excluded: {excluded}')
        print('Fragments:', json.dumps([source[s['start']:s['end']] for s in ranges], ensure_ascii=False))
    print(f'Valid: {valid}/{len(records)}; targeted occurrence checks: {target_checks}/{len(records)}. Semantic scope requires separate inspection.')
    print('Usage:', json.dumps({key: sum(r['usage'][key] for r in records.values()) for key in ('input', 'output', 'cacheRead', 'cacheWrite', 'totalTokens')}, sort_keys=True))


if __name__ == '__main__':
    commands = {'prepare': prepare, 'run': run, 'check': check}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        raise SystemExit('Usage: probe.py prepare|run|check')
    commands[sys.argv[1]]()
