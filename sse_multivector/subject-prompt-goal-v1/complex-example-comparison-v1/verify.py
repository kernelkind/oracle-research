"""Verify the saved comparison without inference, credentials, or held-out inputs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
ROOT = GOAL.parents[1]
sys.path.insert(0, str(ROOT))
from sse_multivector import codex_exec as runner

# Reuse the existing read-only raw-response validator.
spec = importlib.util.spec_from_file_location('existing_verifier', GOAL / 'relation-rule-ablation-v1/verify.py')
existing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(existing)
check, read, sha = existing.check, existing.read, existing.sha
FREEZE = '7b00220'

def frozen(path):
    return subprocess.check_output(['git', 'show', f'{FREEZE}:{path.relative_to(ROOT)}'], cwd=ROOT)

def verify():
    proposal = read(HERE / 'proposal.json')
    check((HERE / 'proposal.json').read_bytes() == frozen(HERE / 'proposal.json'), 'changed proposal')
    paths = [GOAL / 'asv6.21/ASv6.21.md', GOAL / 'asv6.22/ASv6.22.md']
    for path in paths + [ROOT / 'sse_multivector/codex_exec.py', GOAL / 'plan.json']:
        check(path.read_bytes() == frozen(path), f'changed frozen input {path}')
    a, b = [p.read_text() for p in paths]
    check(a.split('</example>', 1)[0] == b.split('</example>', 1)[0], 'changed instructions or first example')
    threads, workdirs, calls = set(), set(), []
    for key in proposal['schedule']:
        condition, label, trial = key.split('-')
        version = 'ASv6.21' if condition == 'base' else 'ASv6.22'
        directory = HERE / key / 'run'
        config_path = HERE / key / 'config.json'
        check(config_path.read_bytes() == frozen(config_path), 'config changed')
        config = runner.SubjectRunnerConfig.load(config_path)
        check(config.subject.model == 'gpt-6-astra' and config.subject.reasoning_effort == 'low', 'model/effort changed')
        check(config.input_path == GOAL / 'astra-examples-comparison-v1/inputs' / f'{label}.json', 'source path changed')
        check(config.input_path.read_bytes() == frozen(config.input_path), 'source bytes changed')
        note, = runner._load_notes(config.input_path)
        manifest = read(directory / 'manifest.json')
        check(manifest == runner._build_subject_manifest(config, 'codex-cli 0.153.0'), 'manifest mismatch')
        check(manifest['subject']['prompt'] == (GOAL / version.lower() / f'{version}.md').read_text().rstrip('\n'), 'prompt mismatch')
        result, = existing.rows(directory / 'results.jsonl')
        check(result['status'] == 'succeeded' and result['attempt'] == 1 and result['exit_code'] == 0, 'failed/retried call')
        check(result['model'] == 'gpt-6-astra' and result['reasoning_effort'] == 'low', 'result settings')
        check(result['manifest_sha256'] == sha((directory / 'manifest.json').read_bytes()), 'manifest hash')
        check(result['prompt_sha256'] == sha(runner._render_subject_prompt(config.subject.prompt, note).encode()), 'rendered prompt hash')
        subjects = existing.verify_payload(result)
        output = read(directory / 'output.json')
        check(output['manifest_sha256'] == result['manifest_sha256'], 'output manifest hash')
        exported, = output['notes']
        check(exported['note_id'] == note.note_id and exported['text'] == note.text, 'output source mismatch')
        check(exported['subjects'] == [{'source_index': i, 'text': s} for i, s in enumerate(subjects)], 'edited output')
        argv = result['argv']
        workdir = argv[argv.index('--cd') + 1]
        check(result['thread_id'] not in threads and workdir not in workdirs, 'reused context within comparison')
        threads.add(result['thread_id']); workdirs.add(workdir)
        for value in ['--ephemeral', '--ignore-user-config', '--ignore-rules', 'web_search="disabled"', 'shell_environment_policy.inherit="none"', 'agents.enabled=false']:
            check(value in argv, f'missing isolation flag {value}')
        check((directory / 'model-instructions.md').read_text() == runner.MINIMAL_MODEL_INSTRUCTIONS, 'model instructions changed')
        calls.append({'key': key, 'version': version, 'note': label, 'trial': int(trial[1:]), 'thread_id': result['thread_id'], 'workdir': workdir, 'subjects': len(subjects), 'usage': result['usage'], 'elapsed_seconds': result['elapsed_seconds']})
    previous_threads, previous_dirs = set(), set()
    previous = GOAL / 'astra-examples-comparison-v1'
    for key in read(previous / 'proposal.json')['schedule']:
        r, = existing.rows(previous / key / 'run/results.jsonl')
        previous_threads.add(r['thread_id'])
        previous_dirs.add(r['argv'][r['argv'].index('--cd') + 1])
    check(not threads & previous_threads and not workdirs & previous_dirs, 'reused prior comparison context')
    runtime = read(HERE / 'runtime.json')
    check(len(calls) == len(runtime['jobs']) == 36, 'call count')
    check(all(j['status'] == 'completed' and j['exit_code'] == 0 for j in runtime['jobs']), 'launcher incomplete')
    check(read(ROOT / 'sse_multivector/atomic-subject-prompt-versions.json')['frozen_atomic_subject_prompt_version'] == 'ASv6.8', 'default changed')
    semantic = None
    if (HERE / 'review.json').exists():
        reviews = read(HERE / 'review.json')['reviews']
        check(len(reviews) == 36 and {r['key'] for r in reviews} == set(proposal['schedule']), 'review output coverage')
        for review in reviews:
            exported, = read(HERE / review['key'] / 'run/output.json')['notes']
            check([s['text'] for s in review['subjects']] == [s['text'] for s in exported['subjects']], 'review text changed')
            check([s['index'] for s in review['subjects']] == list(range(1, len(exported['subjects']) + 1)), 'review indexes')
            for s in review['subjects']:
                check(s['status'] in ['accepted', 'error', 'unresolved'], 'review status')
                if s['status'] != 'accepted':
                    check(bool(s['reason']) and bool(s['evidence']), 'missing review evidence')
        semantic = {'outputs_reviewed': len(reviews), 'subjects_reviewed': sum(len(r['subjects']) for r in reviews), 'saved_review_is_complete': True}
    return {'artifact_verification': 'passed', 'calls': calls, 'unique_threads': len(threads), 'unique_workdirs': len(workdirs), 'previous_comparison_overlap': 0, 'subjects': sum(c['subjects'] for c in calls), 'semantic': semantic, 'limits': ['Verifies saved records and invocation flags, not the opaque service-level context.', 'Prior overlap check covers the immediately preceding 36-call comparison.', 'Mechanical review checks establish completeness, not correctness of semantic judgments.']}

if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
