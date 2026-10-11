"""Opt-in bounded construction; automatic application is not semantic approval."""
import json
from pathlib import Path

try:
    from . import canonical_trial as trial
    from . import experiment as workflow
    from . import extraction_pipeline as engine
    from .bounded_hierarchy_build import _is_case_failure_error, _is_attempt_allowance_error
except ImportError:
    import canonical_trial as trial
    import experiment as workflow
    import extraction_pipeline as engine
    from bounded_hierarchy_build import _is_case_failure_error, _is_attempt_allowance_error


def _failure_receipts(experiment, cases):
    """Failed answers cannot use the successful-response receipt verifier."""
    failed = [c for c in cases if c['status'] == 'failed']
    if not failed:
        return []
    _, config, manifest = workflow.load(experiment)
    records = {workflow.inputs.digest(record): record for record in (
        json.loads(line) for line in (config.run_directory / 'results.jsonl').read_bytes().splitlines())}
    verified = []
    for case in failed:
        receipt = case.get('receipt', {})
        record = records.get(receipt.get('record_sha256'), {})
        identifier = case.get('job_id', case['id'])
        expected = dict(status='failed', stage='prompt', note_id=identifier,
                        job_key='prompt:' + identifier, manifest_sha256=workflow.inputs.digest(manifest),
                        prompt_sha256=engine._sha256_bytes(case['prompt'].encode()),
                        request_sha256=engine._prompt_request_key(manifest, case['prompt']),
                        response_schema_sha256=manifest['response_schema_sha256'],
                        argv=engine._build_exec_argv(config), error=case.get('error'))
        expected.update({key: manifest[key] for key in (
            'provider', 'model', 'reasoning_effort', 'runner_version', 'runner_sha256')})
        if (receipt.get('results_path') != str(config.run_directory / 'results.jsonl')
                or not isinstance(record.get('error'), str)
                or any(record.get(k) != v for k, v in expected.items())):
            return None
        for digest, field in (('stdout', 'stdout_json'), ('stderr', 'stderr'),
                              ('final_output', 'final_output_raw')):
            raw = record.get(field)
            if (raw is None and field != 'final_output_raw') or (raw is not None and not isinstance(raw, str)):
                return None
            if record.get(digest + '_sha256') != (None if raw is None else engine._sha256_bytes(raw.encode())):
                return None
        if record.get('model_result') is not None:
            try:
                result = json.loads(record['stdout_json'])
            except ValueError:
                return None
            if (result != record['model_result'] or result.get('usage') != record.get('usage')
                    or result.get('raw_text') != record.get('final_output_raw')):
                return None
        verified.append(record)
    return verified


def _producer_hold(experiment, cases):
    """Use bound native reviews, including the exact receipt behind reuse."""
    for case in cases:
        reviewed = [(experiment, case)]
        if case.get('reused') and case['status'] == 'valid':
            _, config, manifest = workflow.load(experiment)
            records = (json.loads(line) for line in (config.run_directory / 'results.jsonl').read_bytes().splitlines())
            record = next(r for r in records if workflow.inputs.digest(r) == case['receipt']['record_sha256'])
            reference = record['reused_from']
            source = engine._read_request_source(reference, engine._prompt_request_key(manifest, case['prompt']))
            origin = Path(reference['results_path']).parent.parent
            if (origin / 'experiment.json').exists():
                plan, _, _ = workflow.load(origin)
                source_case = next(c for c in plan['cases']
                                   if c.get('job_id', c['id']) == source['note_id'])
                shown = workflow.report(origin, only=[source_case['id']], include_request_preview=False)['cases'][0]
                if (shown['status'] != 'valid' or shown['receipt']['record_sha256'] != workflow.inputs.digest(source)):
                    raise engine.RunnerError('reused producer review is not bound to the source receipt')
                reviewed.append((origin, shown))
        for origin, shown in reviewed:
            # Native `current` marks matching input/output hashes, not the
            # newest decision. Later verdicts supersede earlier ones per role;
            # a user verdict takes precedence over the latest agent verdict.
            latest = {r['role']: r for r in shown.get('reviews', [])
                      if r.get('current') and r['verdict'] != 'comment'}
            review = latest.get('user', latest.get('agent'))
            if review and review['verdict'] in ('reject', 'uncertain'):
                return (f"automatic hold: current input/output-bound {review['role']} producer "
                        f"review {review['verdict']} at {origin}/{shown['id']}: {review['comment']}")
    return None


def continue_trial(directory, max_nodes, max_new_attempts, attempt_budget_path):
    """Run a finite frozen node range using two irreversible launch counters.

    The local cap covers this continuation across resumes, not each child batch.
    All semantic decisions remain pending; existing advance guards decide holds.
    """
    if any(type(v) is not int or v < 1 for v in (max_nodes, max_new_attempts)):
        raise ValueError('continuation requires positive node and attempt bounds')
    directory = Path(directory).resolve()
    shared_path = Path(attempt_budget_path).resolve()
    control = directory / 'continuation'
    # A separate ownership lock avoids nesting advance_trial's state lock.
    control.mkdir(exist_ok=True)
    with workflow.locked(control):
        state = workflow.read(directory / 'state.json')
        trial._check(state)
        if not state.get('independent_meanings'):
            raise ValueError('continuation requires independently established local meanings')
        shared = engine.PersistentAttemptBudget(shared_path)
        shared.remaining()  # Validate the existing global counter; never initialize it.
        local_path = control / 'attempt-budget.json'
        if shared_path == local_path:
            raise ValueError('shared and continuation attempt budgets must differ')
        local = engine.PersistentAttemptBudget(local_path)
        plan_path = control / 'plan.json'
        if plan_path.exists():
            envelope = workflow.read(plan_path)
            plan = envelope['plan']
            if envelope['sha256'] != workflow.inputs.digest(plan):
                raise ValueError('continuation plan hash differs')
            if (plan['max_nodes'] != max_nodes or plan['max_new_attempts'] != max_new_attempts
                    or plan['attempt_budget'] != str(shared_path)
                    or plan['sources'] != state['sources']
                    or plan['queue_sha256'] != workflow.inputs.digest(
                        state.get('queue', [state['roots'], state.get('children', [])]))):
                raise ValueError('continuation bounds, shared budget, or sources cannot change')
        else:
            if (local_path.exists()
                    or local_path.with_suffix(local_path.suffix + '.claims.jsonl').exists()):
                raise ValueError('missing continuation plan cannot restart frozen bounds')
            count = len(trial.execution_queue(state))
            end = min(count, state['index'] + max_nodes)
            remaining = end - state['index']
            initial_nodes = len(state['nodes'])
            plan = dict(schema_version=1, start_index=state['index'], end_index=end,
                        max_nodes=max_nodes, max_new_attempts=max_new_attempts,
                        attempt_budget=str(shared_path), sources=state['sources'],
                        queue_sha256=workflow.inputs.digest(state.get(
                            'queue', [state['roots'], state.get('children', [])])),
                        maximum_first_attempt_requests=remaining * (1 + initial_nodes)
                        + remaining * (remaining - 1) // 2)
            workflow.write(plan_path, dict(sha256=workflow.inputs.digest(plan), plan=plan))
        local.initialize(max_new_attempts)  # Validates existing usage; cannot reset claims.

        def finish(reason, error=None):
            current = workflow.read(directory / 'state.json')
            result = trial.summary(current)
            result.update(status=reason, stop_reason=reason, semantic_review='pending',
                          start_index=plan['start_index'], end_index=plan['end_index'],
                          attempts=workflow.read(local_path),
                          shared_remaining=shared.remaining(),
                          maximum_first_attempt_requests=plan['maximum_first_attempt_requests'],
                          maximum_attempts_with_one_retry=2 * plan['maximum_first_attempt_requests'])
            if error is not None:
                result['error'] = error
            workflow.write(control / 'report.json', result)
            return result

        while True:
            state = workflow.read(directory / 'state.json')
            trial._check(state)
            if not plan['start_index'] <= state['index'] <= plan['end_index']:
                raise ValueError('trial advanced outside the frozen continuation range')
            if any(step['reviewer'] != 'automatic' for step in state['steps']
                   if plan['start_index'] <= step['index'] < state['index']):
                raise ValueError('manual transition occurred inside automatic continuation')
            if state['status'] == 'complete':
                return finish('complete')
            if state['index'] == plan['end_index']:
                return finish('node_limit')
            if state['experiment'] is None:
                trial.advance_trial(directory, None, 'Resume interrupted native preparation')
                continue
            experiment = Path(state['experiment'])
            if state.get('comparison_policy') and state.get('phase') == 'comparison':
                from .canonical_comparison_policy import checked_cases
                try:
                    checked_cases(state)
                except (ValueError, engine.RunnerError):
                    return finish('invalid_receipt')
            batch = workflow.report(experiment, include_request_preview=False)
            failures = _failure_receipts(experiment, batch['cases'])
            if (any(c['status'] == 'invalid_receipt' for c in batch['cases'])
                    or failures is None):
                return finish('invalid_receipt')
            if any(c.get('failure_kind') == 'provider_fatal' for c in batch['cases']):
                return finish('provider_fatal')
            pending_retry = any(engine.provider_retry_delay(record) is not None for record in failures)
            if pending_retry and min(local.remaining(), shared.remaining()) == 0:
                return finish('attempt_limit')
            if pending_retry or any(c['status'] == 'unrun' for c in batch['cases']):
                error = None
                try:
                    workflow.run(experiment, max_new_attempts=min(local.remaining(), shared.remaining()),
                                 attempt_budget_path=local_path,
                                 additional_attempt_budget_paths=(shared_path,), include_request_preview=False)
                except engine.RunnerError as caught:
                    error = str(caught)
                batch = workflow.report(experiment, include_request_preview=False)
                if (any(c['status'] == 'invalid_receipt' for c in batch['cases'])
                        or _failure_receipts(experiment, batch['cases']) is None):
                    return finish('invalid_receipt', error)
                if any(c.get('failure_kind') == 'provider_fatal' for c in batch['cases']):
                    return finish('provider_fatal', error)
                if error is not None and not _is_case_failure_error(error, batch):
                    reason = ('attempt_limit' if _is_attempt_allowance_error(error)
                              and min(local.remaining(), shared.remaining()) == 0 else 'execution_error')
                    return finish(reason, error)
            cases = batch['cases']
            if any(c['status'] == 'unrun' for c in cases):
                return finish('unrun')
            if any(c['status'] == 'invalid_receipt' for c in cases):
                return finish('invalid_receipt')
            if any(c.get('failure_kind') == 'provider_fatal' for c in cases):
                return finish('provider_fatal')
            if not cases or any(not c.get('receipt') for c in cases):
                return finish('unverified_answer')
            hold = None
            if any(c['status'] != 'valid' for c in cases):
                hold = 'automatic hold: receipt-backed terminal answer failure; semantic review required'
            if state['phase'] == 'meaning':
                hold = hold or _producer_hold(experiment, cases)
            trial.advance_trial(directory, cases[0]['id'],
                                'Automatic receipt/schema/graph checks; semantic review pending.',
                                hold=hold, automatic=True, expected_experiment=str(experiment))
