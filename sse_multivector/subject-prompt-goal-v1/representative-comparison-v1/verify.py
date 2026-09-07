"""Read-only verification of the paired comparison; semantic judgments are not automated."""

from pathlib import Path
import hashlib
import json
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
ROOT = GOAL.parents[1]
sys.path.insert(0, str(ROOT))
from sse_multivector import codex_exec as runner


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def sha(data):
    return hashlib.sha256(data).hexdigest()


plan = read(GOAL / 'plan.json')
comparison = read(HERE / 'comparison.json')
assert sha((GOAL / 'plan.json').read_bytes()) == '64c5e1a8b2897573f4e7f861173fc13a6a9734bda2a40d6d4fb42023d4a1f3fa'
assert sha((GOAL / 'development-input.json').read_bytes()) == comparison['source_sha256']
assert sha((ROOT / plan['unchanged']['runner']).read_bytes()) == plan['unchanged']['runner_sha256']
for name in ['plan.json', 'selection.json', 'development-input.json', 'development-repeat-input.json', 'final-input.json', 'final-repeat-input.json']:
    original = subprocess.check_output(['git', 'show', 'ace3fa2667494f314bcc280f54aaf4c34e242fdc:sse_multivector/subject-prompt-goal-v1/' + name], cwd=ROOT)
    assert (GOAL / name).read_bytes() == original, name
registry = ROOT / 'sse_multivector/atomic-subject-prompt-versions.json'
assert sha(registry.read_bytes()) == '357772ff8c7f673982af976bf43d13a6c4ec5031f6b06ec2361046b9c8e4b95f'
assert read(registry)['frozen_atomic_subject_prompt_version'] == 'ASv6.8'

baseline = read(ROOT / 'sse_multivector/atomic-subject-asv6.11-test-v1/run/manifest.json')
prior_paths = list((ROOT / 'sse_multivector').glob('atomic-subject-*/**/results.jsonl'))
prior_paths += list(GOAL.glob('asv6.*/**/results.jsonl'))
prior = [r for p in prior_paths for r in rows(p)]
prior_threads = {r['thread_id'] for r in prior if r.get('thread_id')}
prior_dirs = {r['argv'][r['argv'].index('--cd') + 1] for r in prior if r.get('argv') and '--cd' in r['argv']}
threads, workdirs = set(), set()
review = read(HERE / 'review.json')
reports = []
all_usage = {}
for version in ['ASv6.13', 'ASv6.17']:
    directory = HERE / version.lower()
    config = runner.SubjectRunnerConfig.load(HERE / (version.lower() + '-config.json'))
    notes = runner._load_notes(config.input_path)
    manifest = read(directory / 'manifest.json')
    manifest_sha = sha((directory / 'manifest.json').read_bytes())
    output = read(directory / 'output.json')
    results = rows(directory / 'results.jsonl')
    reviews = review['versions'][version]['notes']
    assert len(notes) == len(results) == len(output['notes']) == len(reviews) == 28
    assert output['manifest_sha256'] == manifest_sha
    assert config.subject.prompt == (GOAL / version.lower() / (version + '.md')).read_text().removesuffix('\n')
    assert manifest['subject']['prompt'] == config.subject.prompt
    assert manifest['input_sha256'] == comparison['source_sha256']
    for key in ['wrapper_sha256', 'isolation', 'codex_binary', 'codex_version', 'subject_envelope_version', 'subject_input_normalization_version']:
        assert manifest[key] == baseline[key], key
    for key in ['model', 'reasoning_effort', 'response_schema', 'response_schema_sha256']:
        assert manifest['subject'][key] == baseline['subject'][key], key
    assert sha((directory / 'model-instructions.md').read_bytes()) == manifest['isolation']['model_instructions_sha256']
    assert read(directory / 'subject-output-schema.json') == manifest['subject']['response_schema']
    usage = {}
    for index, (note, result, exported, judged) in enumerate(zip(notes, results, output['notes'], reviews)):
        assert note.note_id == result['note_id'] == exported['note_id'] == judged['note_id']
        assert note.text == exported['text']
        assert judged['label'] == f'D{index + 1:02d}'
        assert result['status'] == 'succeeded' and result['exit_code'] == 0 and result['attempt'] == 1
        assert result['manifest_sha256'] == manifest_sha
        assert result['wrapper_sha256'] == manifest['wrapper_sha256']
        assert result['model'] == 'gpt-5.6-sol' and result['reasoning_effort'] == 'low'
        assert result['prompt_sha256'] == sha(runner._render_subject_prompt(config.subject.prompt, note).encode())
        for raw, digest in [('final_output_raw', 'final_output_sha256'), ('stdout_jsonl', 'stdout_sha256'), ('stderr', 'stderr_sha256')]:
            assert sha(result[raw].encode()) == result[digest]
        assert json.loads(result['final_output_raw'])['subjects'] == result['response'] == [s['text'] for s in exported['subjects']]
        assert [s['source_index'] for s in exported['subjects']] == list(range(len(result['response'])))
        events = [json.loads(line) for line in result['stdout_jsonl'].splitlines()]
        assert sum(e['type'] == 'turn.started' for e in events) == 1
        assert sum(e['type'] == 'turn.completed' for e in events) == 1
        assert all(e['item']['type'] == 'agent_message' for e in events if 'item' in e)
        assert [e['thread_id'] for e in events if e['type'] == 'thread.started'] == [result['thread_id']]
        argv = result['argv']
        assert all(flag in argv for flag in ['--ephemeral', '--ignore-rules', '--ignore-user-config', '--strict-config'])
        assert 'resume' not in argv and 'web_search="disabled"' in argv
        directory_used = argv[argv.index('--cd') + 1]
        assert directory_used not in workdirs and directory_used not in prior_dirs
        assert result['thread_id'] not in threads and result['thread_id'] not in prior_threads
        threads.add(result['thread_id'])
        workdirs.add(directory_used)
        assert [{k: s[k] for k in ['source_index', 'text']} for s in judged['subjects']] == exported['subjects']
        assert judged['coverage'] in ['accepted', 'error', 'unresolved'] and judged['coverage_reason']
        for subject in judged['subjects']:
            assert subject['status'] in ['accepted', 'error', 'unresolved']
            if subject['status'] != 'accepted':
                assert subject.get('reason') and subject.get('evidence')
        for key, value in result['usage'].items():
            usage[key] = usage.get(key, 0) + value
            all_usage[key] = all_usage.get(key, 0) + value
    reports.append({'version': version, 'calls': len(results), 'subjects': sum(len(n['subjects']) for n in reviews), 'accepted_subjects': sum(s['status'] == 'accepted' for n in reviews for s in n['subjects']), 'clean_notes': sum(n['coverage'] == 'accepted' and all(s['status'] == 'accepted' for s in n['subjects']) for n in reviews), 'manifest_sha256': manifest_sha, 'usage': usage})

runtime = read(HERE / 'runtime.json')
completed = [c for c in runtime['calls'] if c.get('exit_code') == 0]
expected_order = [(f'D{n:02d}', v) for n in range(1, 29) for v in (['ASv6.13', 'ASv6.17'] if n % 2 else ['ASv6.17', 'ASv6.13'])]
assert [(c['note'], c['prompt']) for c in completed] == expected_order
assert len(threads) == len(workdirs) == comparison['calls'] == 56
for call in completed:
    h = call['before']
    assert h['available_kib'] >= 16 * 1024 * 1024 and h['memory_avg10'] <= 1 and h['io_avg10'] <= 10
    assert call['session_id'] is None and call['observations']
    assert all(flag in call['command'] for flag in ['MemoryMax=2G', 'MemorySwapMax=0', 'RuntimeMaxSec=900', '--max-new-jobs 1'])
for earlier, later in zip(completed, completed[1:]):
    assert earlier['finished_utc'] <= later['started_utc']
print(json.dumps({'schema_version': 1, 'comparison': reports, 'unique_threads': len(threads), 'unique_workdirs': len(workdirs), 'prior_calls_checked_for_reuse': len(prior), 'one_turn_each': True, 'no_tool_events': True, 'exact_prompts_inputs_and_raw_hashes_verified': True, 'all_outputs_have_recorded_semantic_review': True, 'paired_order_and_sequential_admission_verified': True, 'original_plan_and_final_inputs_unchanged': True, 'frozen_registry_unchanged': True, 'usage': all_usage, 'limitation': 'This verifies provenance and review completeness, not semantic correctness. One paired run does not satisfy repeated-development or untouched final validation.'}, indent=2))
