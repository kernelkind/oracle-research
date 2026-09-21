"""Prepare this six-case probe offline; never sends a model request."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    plan = json.loads((HERE / 'plan.json').read_text())
    baseline = (HERE / plan['baseline_prompt']).read_bytes()
    assert hashlib.sha256(baseline).hexdigest() == plan['baseline_sha256']
    template = (HERE / plan['prompt_file']).read_bytes().decode('utf-8')
    restored = template
    for edit in json.loads((HERE / 'edits.json').read_text())['edits']:
        assert restored.count(edit['new']) == 1
        restored = restored.replace(edit['new'], edit['old'])
    assert restored.encode('utf-8') == baseline, 'semantic instructions changed'
    cases = json.loads((HERE / 'cases.json').read_text())
    prior = json.loads((HERE.parent / 'position-selection-v1/config.json').read_text())
    config = {key: value for key, value in prior.items() if key != 'prompts'}
    config['run_directory'] = plan['run_directory']
    config['auth_file'] = plan['auth_file']
    config['prompts'] = []
    for case in cases:
        fixtures = json.loads((HERE / case['source_fixture']).read_text())
        source = next(item['source'] for item in fixtures if item['id'] == case['source_id'])
        assert '⟦' not in source and '⟧' not in source
        indexed = ''.join(f'[{i}]{char}' for i, char in enumerate(source)) + f'[{len(source)}]'
        prompt = template.replace('{POST}', source).replace('{INDEXED_POST}', indexed).replace('{SUBJECT}', case['subject'])
        assert all(token not in prompt for token in ('{POST}', '{INDEXED_POST}', '{SUBJECT}', '⟦', '⟧'))
        config['prompts'].append({'prompt_id': case['id'], 'text': prompt})
    assert len(config['prompts']) == plan['calls'] == 6
    assert config['provider'] == 'openai-codex'
    assert config['model'] == plan['model'] and config['reasoning_effort'] == plan['reasoning_effort']
    encoded = json.dumps(config, ensure_ascii=False, indent=2) + '\n'
    target = HERE / plan['config_file']
    if target.exists():
        assert target.read_bytes() == encoded.encode('utf-8'), 'existing config differs'
    else:
        with target.open('x', encoding='utf-8') as output:
            output.write(encoded)
    print('Prepared six prompts. Semantic instructions unchanged; no highlights or expected answers included.')


if __name__ == '__main__':
    main()
