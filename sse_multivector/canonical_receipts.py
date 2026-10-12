"""Validate native failed-call receipts and bound producer reviews."""
import json
from pathlib import Path

try:
    from . import experiment as workflow
    from . import extraction_pipeline as engine
except ImportError:
    import experiment as workflow
    import extraction_pipeline as engine


def _failure_receipts(experiment, cases):
    """Failed answers cannot use the successful-response receipt verifier."""
    failed = [c for c in cases if c['status'] == 'failed']
    if not failed:
        return []
    _, config, manifest = workflow.load(experiment)
    records = workflow.result_records(config.run_directory / 'results.jsonl')
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
    with workflow.report_scope() as files:
        for case in cases:
            reviewed = [(experiment, case)]
            if case.get('reused') and case['status'] == 'valid':
                _, config, manifest = workflow.load(experiment)
                record = workflow.result_records(config.run_directory / 'results.jsonl')[case['receipt']['record_sha256']]
                reference = record['reused_from']
                source = engine._read_request_source(reference, engine._prompt_request_key(manifest, case['prompt']),
                                                    files=files)
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
