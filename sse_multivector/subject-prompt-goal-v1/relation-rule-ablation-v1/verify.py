"""Read-only verification; a valid partial prefix is not a completed comparison.

Run while the artifacts are quiescent. This script does not call Codex, read
credentials, write files, judge meaning, or decide the semantic stopping rule.
"""

from datetime import datetime
import hashlib
import json
from pathlib import Path
import shlex
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
ROOT = GOAL.parents[1]
FROZEN_COMMIT = 'bd0fb4089a09d908c4516ace1b29718d9c333c39'
sys.path.insert(0, str(ROOT))
from sse_multivector import generation_history as runner


def check(condition, message):
    # Unlike an assert statement, this remains effective with python -O.
    if not condition:
        raise AssertionError(message)


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def frozen_bytes(path):
    return runner.source_at_revision(path, FROZEN_COMMIT)


def verify_payload(result):
    """Check saved raw hashes, response strings, thread, usage and stdout agreement."""
    for raw, digest in [('final_output_raw', 'final_output_sha256'),
                        ('stdout_jsonl', 'stdout_sha256'), ('stderr', 'stderr_sha256')]:
        check(isinstance(result[raw], str), f'{raw}: expected a string')
        check(sha(result[raw].encode()) == result[digest], f'{digest}: mismatch')
    raw = json.loads(result['final_output_raw'])
    check(isinstance(raw, dict) and set(raw) == {'subjects'}, 'raw response schema')
    subjects = runner._validate_string_array(raw['subjects'], 'subjects', allow_empty=True)
    check(subjects == result['response'], 'raw/response subject mismatch')
    events = [json.loads(line) for line in result['stdout_jsonl'].splitlines() if line.strip()]
    thread, usage = runner._parse_event_stream(result['stdout_jsonl'])
    check(thread == result['thread_id'], 'stdout thread mismatch')
    check(usage == result['usage'], 'stdout usage mismatch')
    check(isinstance(usage, dict) and bool(usage), 'missing usage')
    check(all(isinstance(v, int) and not isinstance(v, bool) and v >= 0
              for v in usage.values()), 'invalid token usage')
    starts = [i for i, e in enumerate(events) if e['type'] == 'turn.started']
    ends = [i for i, e in enumerate(events) if e['type'] == 'turn.completed']
    check(len(starts) == len(ends) == 1 and starts[0] < ends[0], 'expected one turn')
    check(events[0]['type'] == 'thread.started' and ends[0] == len(events) - 1,
          'event stream boundaries')
    allowed = {'thread.started', 'turn.started', 'turn.completed',
               'item.started', 'item.updated', 'item.completed'}
    check(all(e['type'] in allowed for e in events), 'unexpected event type')
    for i, event in enumerate(events):
        if event['type'].startswith('item.'):
            check(starts[0] < i < ends[0], 'item outside turn')
            check(event['item']['type'] == 'agent_message', 'tool/non-message event')
    messages = [e['item']['text'] for e in events if e['type'] == 'item.completed']
    check(bool(messages), 'missing completed agent message')
    check(json.loads(messages[-1]) == raw, 'stdout/final response mismatch')
    return subjects


def verify_review(review, saved_notes, selections):
    """Validate supplied judgments and report, rather than assume, completeness."""
    if review is None:
        return {'review_present': False, 'reviewed_outputs': 0,
                'all_outputs_have_recorded_semantic_review': False}
    check(review['schema_version'] == 1, 'review schema')
    seen_runs, reviewed = set(), set()
    for run in review['runs']:
        key = (run['version'], run['trial'])
        check(key in saved_notes and key not in seen_runs, 'unknown/duplicate review run')
        seen_runs.add(key)
        available = saved_notes[key]
        check(len(run['notes']) <= len(available), 'review extends beyond saved outputs')
        for index, judged in enumerate(run['notes']):
            exported = available[index]
            check(judged['note_id'] == exported['note_id'], 'review note/order mismatch')
            check(judged['label'] == selections[index]['label'], 'review label mismatch')
            check([{k: s[k] for k in ['source_index', 'text']} for s in judged['subjects']]
                  == exported['subjects'], 'review subject mismatch')
            check(judged['coverage'] in ['accepted', 'error', 'unresolved'], 'coverage status')
            check(isinstance(judged['coverage_reason'], str)
                  and judged['coverage_reason'].strip(), 'missing coverage reason')
            for subject in judged['subjects']:
                check(subject['status'] in ['accepted', 'error', 'unresolved'], 'subject status')
                if subject['status'] != 'accepted':
                    check(bool(subject.get('reason')) and bool(subject.get('evidence')),
                          'nonaccepted subject lacks reason/evidence')
            reviewed.add((*key, exported['note_id']))
    expected = {(*key, note['note_id']) for key, notes in saved_notes.items() for note in notes}
    return {'review_present': True, 'reviewed_outputs': len(reviewed),
            'all_outputs_have_recorded_semantic_review': bool(expected) and reviewed == expected}


def expected_schedule(proposal):
    versions = proposal['design']['prompts']
    return [(trial, entry['label'], version)
            for trial in range(1, proposal['design']['trials'] + 1)
            for index, entry in enumerate(proposal['selection'])
            for version in (versions if (index + trial) % 2 == 1 else versions[::-1])]


def verify_runtime(runtime, proposal, plan, results_by_call):
    """Check recorded launch/result consistency, not independent execution order."""
    if runtime is None:
        check(not results_by_call, 'results without runtime record')
        return {'runtime_present': False, 'recorded_calls': 0, 'terminal_calls': 0,
                'pending_calls': 0, 'recorded_schedule_consistency_verified': False}
    check(runtime['schema_version'] == 1, 'runtime schema')
    check(runtime['plan_commit'] == FROZEN_COMMIT, 'runtime plan commit')
    calls = runtime['calls']
    expected = expected_schedule(proposal)
    actual = [(c['trial'], c['note'], c['prompt']) for c in calls]
    check(len(actual) <= len(expected) and actual == expected[:len(actual)],
          'runtime is not the planned schedule prefix')
    check(set(results_by_call).issubset(actual), 'unrecorded call result')
    terminal, pending, units = 0, 0, set()
    previous_finish = None
    for index, call in enumerate(calls):
        key = actual[index]
        position = next(i + 1 for i, n in enumerate(proposal['selection'])
                        if n['label'] == call['note'])
        check(call['position'] == position, 'runtime position mismatch')
        check(call['unit'] not in units, 'duplicate launcher unit')
        units.add(call['unit'])
        before = call['before']
        check(before['available_kib'] >= 16 * 1024 * 1024
              and 0 <= before['memory_avg10'] <= 1 and 0 <= before['io_avg10'] <= 10,
              'admission pressure exceeds frozen limits')
        command = shlex.split(call['command'])
        config = HERE / f"{call['prompt'].lower()}-trial{call['trial']}-config.json"
        check(command[:4] == ['systemd-run', '--user', '--wait', '--pipe'], 'launcher prefix')
        check(command[4:10] == ['--collect', f"--unit={call['unit']}",
              '--property=MemoryMax=2G', '--property=MemorySwapMax=0',
              '--property=RuntimeMaxSec=900', f'--working-directory={ROOT}'], 'launcher limits')
        check(len(command) == 16 and Path(command[10]).name.startswith('python'),
              'launcher interpreter/arguments')
        check(command[-5:] == [plan['unchanged']['runner'], 'subjects',
              str(config.relative_to(ROOT)), '--max-new-jobs', '1'], 'launcher runner/config')
        started = datetime.fromisoformat(call['started_utc'])
        check(previous_finish is None or previous_finish <= started, 'overlapping recorded calls')
        if 'exit_code' not in call:
            pending += 1
            check(index == len(calls) - 1 and 'finished_utc' not in call,
                  'nonterminal call must be last')
            continue
        terminal += 1
        check(call['exit_code'] == 0 and call['session_id'] is None, 'unsuccessful launcher')
        check(key in results_by_call, 'terminal launcher lacks result')
        check(bool(call['observations']), 'missing running pressure observations')
        for observation in call['observations']:
            check(observation['available_kib'] >= 0 and observation['memory_avg10'] >= 0
                  and observation['io_avg10'] >= 0, 'invalid pressure observation')
        finished = datetime.fromisoformat(call['finished_utc'])
        check(started <= finished, 'negative recorded duration')
        previous_finish = finished
        statuses = [json.loads(line) for line in call['output'].splitlines()
                    if line.lstrip().startswith('{')]
        check(len(statuses) == 1, 'expected one launcher status')
        status = statuses[0]
        check(status['new_jobs'] == 1 and status['completed_notes'] == position,
              'launcher status count mismatch')
        check(status['complete'] is (position == len(proposal['selection'])),
              'launcher completion flag mismatch')
    return {'runtime_present': True, 'recorded_calls': len(calls),
            'terminal_calls': terminal, 'pending_calls': pending,
            'recorded_schedule_consistency_verified': True}


def verify():
    preflight_path = HERE / 'preflight.json'
    check(preflight_path.read_bytes() == frozen_bytes(preflight_path), 'changed frozen preflight')
    preflight = read(preflight_path)
    for group in ['frozen_sha256', 'protected_sha256']:
        for relative, digest in preflight[group].items():
            path = ROOT / relative
            check(sha(runner.source_bytes(path)) == digest, f'{group}: {relative}')
            check(sha(frozen_bytes(path)) == digest, f'freeze commit mismatch: {relative}')
    plan, proposal = read(GOAL / 'plan.json'), read(HERE / 'proposal.json')
    versions, trials = proposal['design']['prompts'], proposal['design']['trials']
    check(versions == ['ASv6.13', 'ASv6.20'] and trials == 3, 'frozen comparison design')
    check(proposal['design']['max_new_calls'] == 36, 'frozen call ceiling')
    control = (GOAL / 'asv6.13/ASv6.13.md').read_text()
    candidate = (GOAL / 'asv6.20/ASv6.20.md').read_text()
    removed = ' ' + ' '.join(proposal['removed'])
    check(control.count(removed) == 1 and candidate == control.replace(removed, ''),
          'not the exact two-sentence ablation')
    registry = read(GOAL / 'asv6.20/subject-prompts.json')
    check(registry['frozen_atomic_subject_prompt_version'] == 'ASv6.13', 'local selector')
    check(read(ROOT / 'sse_multivector/atomic-subject-prompt-versions.json')
          ['frozen_atomic_subject_prompt_version'] == 'ASv6.8', 'canonical selector')
    notes = runner._load_notes(HERE / 'input.json')
    check(len(notes) == len(proposal['selection']) == 6, 'selected note count')
    for note, entry in zip(notes, proposal['selection']):
        sources = {n.note_id: n.text for n in runner._load_notes(HERE / entry['source'])}
        check(note.note_id == entry['note_id'] and sources[note.note_id] == note.text,
              'selected note/source mismatch')

    # Hash every inspected mutable artifact again at the end; never claim a
    # consistent snapshot if a producer changes those files during inspection.
    snapshots = {}

    def artifact(path):
        payload = path.read_bytes() if path.exists() else None
        snapshots[path] = None if payload is None else sha(payload)
        return payload

    runtime_raw = artifact(HERE / 'runtime.json')
    runtime = None if runtime_raw is None else json.loads(runtime_raw)
    review_raw = artifact(HERE / 'review.json')
    review = None if review_raw is None else json.loads(review_raw)
    prior_threads, prior_dirs, prior_calls = set(), set(), 0
    prior_paths = sorted(p for p in (ROOT / 'sse_multivector').rglob('results.jsonl')
                         if not p.is_relative_to(HERE))
    for path in prior_paths:
        for result in rows(path):
            prior_calls += 1
            if result.get('thread_id'):
                prior_threads.add(result['thread_id'])
            argv = result.get('argv', [])
            if '--cd' in argv:
                prior_dirs.add(argv[argv.index('--cd') + 1])
    prior_inventory = [{'path': str(p.relative_to(ROOT)), 'sha256': sha(p.read_bytes())}
                       for p in prior_paths]
    threads, workdirs, reports, usage, saved_notes, results_by_call = set(), set(), [], {}, {}, {}
    codex_version = 'codex-cli 0.153.0'
    specs = [(v, t) for t in range(1, trials + 1) for v in versions]
    expected_run_names = {f'{v.lower()}-trial{t}' for v, t in specs}
    check(all(p.parent.name in expected_run_names for p in HERE.rglob('results.jsonl')),
          'unexpected result directory')
    for version, trial in specs:
        name = f'{version.lower()}-trial{trial}'
        directory = HERE / name
        config = runner.SubjectRunnerConfig.load(HERE / (name + '-config.json'))
        check(config.input_path == HERE / 'input.json' and config.run_directory == directory,
              'config input/run directory')
        check(str(config.codex_binary) == plan['unchanged']['codex_binary']
              and str(config.codex_home) == plan['unchanged']['codex_home'], 'binary/account')
        check(config.subject.model == plan['unchanged']['model']
              and config.subject.reasoning_effort == plan['unchanged']['reasoning_effort'],
              'model/effort')
        check(config.subject.prompt_version == version, 'prompt version')
        check(config.subject.prompt == (GOAL / version.lower() / (version + '.md'))
              .read_text().removesuffix('\n'), 'prompt bytes')
        artifacts = {n: artifact(directory / n) for n in ['manifest.json', 'results.jsonl',
                     'output.json', 'model-instructions.md', 'subject-output-schema.json']}
        manifest_raw = artifacts['manifest.json']
        saved_notes[(version, trial)] = []
        if manifest_raw is None:
            check(all(v is None for v in artifacts.values()), 'artifacts without manifest')
            reports.append({'version': version, 'trial': trial, 'calls': 0,
                            'run_complete': False, 'export_present': False})
            continue
        manifest, manifest_sha = json.loads(manifest_raw), sha(manifest_raw)
        check(manifest == runner._build_subject_manifest(config, codex_version), 'manifest mismatch')
        check(artifacts['model-instructions.md'] is not None
              and sha(artifacts['model-instructions.md']) == manifest['isolation']
              ['model_instructions_sha256'], 'model instructions mismatch')
        check(artifacts['subject-output-schema.json'] is not None
              and json.loads(artifacts['subject-output-schema.json']) == runner.SUBJECT_SCHEMA,
              'output schema mismatch')
        result_raw = artifacts['results.jsonl']
        results = [] if result_raw is None else [json.loads(line) for line in
                  result_raw.decode().splitlines() if line.strip()]
        check(len(results) <= len(notes), 'too many results/retries')
        for index, result in enumerate(results):
            note = notes[index]
            label = proposal['selection'][index]['label']
            check(result['schema_version'] == 1 and result['note_id'] == note.note_id,
                  'result note/schema/order mismatch')
            check(result['stage'] == 'subject' and result['job_key'] ==
                  runner._job_key('subject', note.note_id, None), 'result stage/job')
            check(result['status'] == 'succeeded' and result['exit_code'] == 0
                  and result['attempt'] == 1 and result['error'] is None,
                  'failed/retried result (preserve and audit separately)')
            check('retry_reason' not in result and 'reuse_source' not in result, 'retry/reuse metadata')
            for key, expected in {'manifest_sha256': manifest_sha,
                                  'wrapper_sha256': manifest['wrapper_sha256'],
                                  'model': config.subject.model,
                                  'reasoning_effort': config.subject.reasoning_effort,
                                  'codex_version': codex_version,
                                  'response_schema_sha256': manifest['subject']['response_schema_sha256'],
                                  'prompt_sha256': sha(runner._render_subject_prompt(
                                      config.subject.prompt, note).encode())}.items():
                check(result[key] == expected, f'result {key} mismatch')
            subjects = verify_payload(result)
            argv = result['argv']
            check(argv.count('--cd') == 1, 'workdir flag')
            workspace = Path(argv[argv.index('--cd') + 1])
            check(workspace.parent == config.codex_home / 'job-workspaces'
                  and workspace.name.startswith('subject-'), 'sterile workdir path')
            check(argv == runner._build_exec_argv(config, config.subject, workspace,
                  directory / 'subject-output-schema.json', workspace / 'response.json'),
                  'argv differs from production isolated invocation')
            check(str(workspace) not in workdirs and str(workspace) not in prior_dirs,
                  'reused workdir')
            check(result['thread_id'] not in threads and result['thread_id'] not in prior_threads,
                  'reused thread')
            threads.add(result['thread_id'])
            workdirs.add(str(workspace))
            for key, value in result['usage'].items():
                usage[key] = usage.get(key, 0) + value
            saved_notes[(version, trial)].append({'note_id': note.note_id, 'text': note.text,
                'subjects': [{'source_index': i, 'text': s} for i, s in enumerate(subjects)]})
            results_by_call[(trial, label, version)] = result
        export_present = artifacts['output.json'] is not None
        if export_present:
            check(len(results) == len(notes), 'full export with partial results')
            check(json.loads(artifacts['output.json']) == {'schema_version': 1,
                  'manifest_sha256': manifest_sha, 'notes': saved_notes[(version, trial)]},
                  'raw/export mismatch')
        elif len(results) == len(notes):
            # The final raw record precedes export creation during an active call.
            pending = [] if runtime is None else [c for c in runtime['calls'] if 'exit_code' not in c]
            check(any(c['prompt'] == version and c['trial'] == trial for c in pending),
                  'completed run lacks export')
        reports.append({'version': version, 'trial': trial, 'calls': len(results),
                        'run_complete': len(results) == len(notes) and export_present,
                        'export_present': export_present, 'manifest_sha256': manifest_sha})
    runtime_report = verify_runtime(runtime, proposal, plan, results_by_call)
    review_report = verify_review(review, saved_notes, proposal['selection'])
    for path, digest in snapshots.items():
        now = sha(path.read_bytes()) if path.exists() else None
        check(now == digest, 'artifacts changed during verification; retry when quiescent')
    full_generation = len(results_by_call) == 36 and runtime_report['terminal_calls'] == 36
    return {'schema_version': 1, 'artifact_verification': 'passed',
            'snapshot_stable': True, 'frozen_commit': FROZEN_COMMIT,
            'generation_state': 'all_three_trials_complete' if full_generation else 'partial',
            'all_planned_calls_complete': full_generation,
            'first_two_trials_complete': all(r['run_complete'] for r in reports if r['trial'] <= 2)
                and runtime_report['terminal_calls'] >= 24,
            'planned_call_ceiling': 36, 'successful_calls': len(results_by_call),
            'comparison': reports, 'unique_threads': len(threads), 'unique_workdirs': len(workdirs),
            'prior_calls_checked_for_reuse': prior_calls,
            'prior_result_files': len(prior_paths), 'prior_inventory': prior_inventory,
            'one_turn_each': True, 'no_tool_events': True,
            'exact_prompts_inputs_and_raw_hashes_verified': True,
            'stdout_response_and_usage_agreement_verified': True,
            'present_exports_agree_with_raw_results': True,
            'frozen_and_protected_hashes_verified': True,
            **runtime_report, **review_report, 'usage': usage,
            'semantic_decision_verified': False, 'fixed_validation_pass_verified': False,
            'limitations': [
                'Artifact-valid partial results do not prove completion or authorize final validation.',
                'Runtime commands, statuses and timestamps are mutually consistent records, not an '
                'independent link from launcher order to result thread IDs or proof of actual order.',
                'Recorded observations do not independently establish continuous host-resource '
                'monitoring, process isolation or provider-side limits.',
                'Review completeness checks exact subjects and judgment fields, not semantic '
                'correctness, identity hiding, the two-trial stopping rule or the retain/reject decision.',
                'Prior reuse checks cover the recorded sse_multivector results inventory only.',
            ]}


if __name__ == '__main__':
    try:
        print(json.dumps(verify(), indent=2))
    except (AssertionError, KeyError, OSError, ValueError, runner.RunnerError) as error:
        print(json.dumps({'schema_version': 1, 'artifact_verification': 'failed',
                          'all_planned_calls_complete': False, 'error': str(error)}))
        sys.exit(1)
