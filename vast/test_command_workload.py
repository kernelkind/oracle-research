import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

import package
import runner
from test_generalization import FAKE_COMMAND


class CommandWorkloadTest(unittest.TestCase):
    def test_unbounded_stop_refuses_before_ssh_without_complete_review(self):
        self.freeze()
        self.context.config['workload']['work_seconds'] = None
        runner.atomic_json(self.root / 'launch/create-result.json', {'success': True, 'new_contract': 42})
        with mock.patch.object(self.module, 'ensure_ssh', side_effect=AssertionError('stop attempted SSH')), \
                mock.patch.object(self.module, 'destroy_instance', side_effect=AssertionError('stop attempted deletion')):
            with self.assertRaisesRegex(self.module.OperationError, 'complete.*review'):
                self.module.stop(self.context)

    def test_unbounded_watch_never_stops_on_expiry_error_or_interrupt(self):
        self.spec['limits']['work_seconds'] = None
        self.freeze()
        runner.atomic_json(self.root / 'launch/watch-deadline.json', {'deadline_utc': '2000-01-01T00:00:00Z'})
        runner.atomic_bytes(self.root / 'launch/create-request-attempted.txt', b'attempted')
        with mock.patch.object(self.module, 'run', return_value={'state': 'retrieved'}) as run, \
                mock.patch.object(self.module, 'stop') as stop:
            self.assertEqual(self.module.run_watch(self.context, None)['state'], 'retrieved')
        run.assert_called_once()
        stop.assert_not_called()
        for error in (ValueError('provider error'), KeyboardInterrupt()):
            with mock.patch.object(self.module, 'run', side_effect=error), \
                    mock.patch.object(self.module, 'stop') as stop:
                with self.assertRaises(type(error)):
                    self.module.run_watch(self.context, None)
            stop.assert_not_called()

    def test_unbounded_real_worker_has_no_inherited_deadline(self):
        self.spec['limits']['work_seconds'] = None
        self.spec['environment']['ORACLE_RUN_DEADLINE_UTC'] = '2000-01-01T00:00:00Z'
        self.spec['command'] = [sys.executable, '-c',
            "from pathlib import Path; import os,json; Path('output.txt').write_text(json.dumps(os.environ.get('ORACLE_RUN_DEADLINE_UTC')))"]
        self.freeze()
        self.assertEqual(self.prepare_and_run()['exit_status'], 0)
        self.assertIsNone(json.loads((self.root / 'work/output.txt').read_text()))

    def test_unbounded_remote_stop_requires_user_approval_before_signal(self):
        self.spec['limits']['work_seconds'] = None
        self.freeze()
        with mock.patch.object(self.module, 'remote_attempt_status', return_value={'state': 'running', 'controller_pid': 123}), \
                mock.patch.object(self.module, 'process_alive', return_value=True), \
                mock.patch.object(self.module.os, 'killpg') as signal_job:
            with self.assertRaisesRegex(self.module.OperationError, 'user stop approval'):
                self.module.remote_stop(self.context, '001')
            signal_job.assert_not_called()
            self.module.remote_stop(self.context, '001', 'User approved stopping the incomplete test workload')
            signal_job.assert_called_once()
        self.assertTrue((self.root / 'work/full-build-attempts/001/user-approved-stop.json').exists())

    def test_unbounded_destroy_requires_complete_review_before_provider_call(self):
        self.spec['limits']['work_seconds'] = None
        self.freeze()
        with mock.patch.object(self.module, 'sanitized_live_instances', side_effect=AssertionError('deletion reached provider')):
            with self.assertRaisesRegex(self.module.OperationError, 'complete.*review'):
                self.module.destroy_instance(self.context, '42')

    def test_unbounded_retrieval_requires_review_and_unchanged_complete_local_files(self):
        self.spec['limits']['work_seconds'] = None
        fixture = self.lifecycle_fixture()
        self.assertEqual(fixture.invoke_with_tty_secret('run').returncode, 0)
        fixture.set_provider(remote_status='terminal', remote_terminal_kind='full-build.exit')
        self.assertEqual(fixture.invoke('run', '--watch').returncode, 0)
        missing = fixture.invoke('stop')
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn('completion review', missing.stderr)
        self.assertEqual(fixture.provider()['destroy_calls'], 0)
        receipt = self.root / 'launch/retrieval-verification.json'
        runner.atomic_json(self.root / 'launch/completion-review.json', {
            'complete': True, 'instance_id': runner.read_json(receipt)['instance_id'],
            'operation_contract_sha256': runner.sha256_file(self.config),
            'retrieval_verification_sha256': runner.sha256_file(receipt),
            'checks': ['Required output and worker evidence are complete and saved locally.']})
        output = self.root / 'result/work/result.bin'
        saved = output.read_bytes()
        output.unlink()
        incomplete = fixture.invoke('stop')
        self.assertNotEqual(incomplete.returncode, 0)
        self.assertEqual(fixture.provider()['destroy_calls'], 0)
        output.write_bytes(saved)
        stopped = fixture.invoke('stop')
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(fixture.provider()['destroy_calls'], 1)

    def test_unbounded_incomplete_stop_records_explicit_user_approval(self):
        self.spec['limits']['work_seconds'] = None
        fixture = self.lifecycle_fixture()
        self.assertEqual(fixture.invoke_with_tty_secret('run').returncode, 0)
        reason = 'User approved stopping this incomplete test workload after reviewing missing data.'
        stopped = fixture.invoke('stop', '--incomplete-stop-approval', reason)
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(fixture.provider()['destroy_calls'], 1)
        self.assertEqual(runner.read_json(self.root / 'launch/user-approved-incomplete-stop.json')['reason'], reason)

    def test_progressive_inventory_includes_only_published_files(self):
        self.spec['outputs'] = ['results']
        self.spec['progressive_copy'] = {'poll_seconds': 1, 'bytes_per_second': 65536, 'timeout_seconds': 30}
        self.freeze()
        note = self.root / 'work/results/student/baseline/note-0000'
        note.mkdir(parents=True)
        (note / 'subjects.json').write_text('raw response')
        (note / 'subjects-result.json').write_text('parsed response')
        seal = {name: runner.sha256_file(note / name) for name in ('subjects.json', 'subjects-result.json')}
        runner.atomic_json(note / 'complete.json', seal)
        partial = self.root / 'work/results/student/checkpoints/checkpoint-200.partial-1'
        partial.mkdir(parents=True)
        (partial / 'weights').write_text('not yet published')
        runner.atomic_json(partial / 'complete.json', {'weights': runner.sha256_file(partial / 'weights')})
        records = self.call('_remote-progress')['files']
        self.assertEqual({r['path'] for r in records},
            {str((note / name).relative_to(self.root)) for name in (*seal, 'complete.json')})
        self.assertEqual(self.context.config['workload']['progressive_copy'], self.spec['progressive_copy'])

    def test_copy_receive_retains_partial_bytes_and_resumes_without_rewriting_verified_files(self):
        import hashlib
        self.spec['progressive_copy'] = {'poll_seconds': 1, 'bytes_per_second': 65536, 'timeout_seconds': 30}
        self.freeze()
        payload = b'first response' * 100
        record = {'path': 'work/results/subject.json', 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}
        request = self.root / 'request.json'
        runner.atomic_json(request, [record])
        command = [sys.executable, '-B', str(self.operator), '--root', str(self.root), '--config', str(self.config),
                   '_receive-copy', '--request', str(request)]
        failed = subprocess.run(command, input=payload[:100], capture_output=True, timeout=20)
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn(b'ended early', failed.stderr)
        self.assertEqual((self.root / 'progressive/partial'/record['path']).read_bytes(), payload[:100])
        self.assertFalse((self.root / 'result.next'/record['path']).exists())
        runner.atomic_json(request, [{**record, 'offset': 100}], replace=True)
        resumed = subprocess.run(command, input=payload[100:], capture_output=True, timeout=20)
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        target = self.root / 'result.next'/record['path']
        self.assertEqual(target.read_bytes(), payload)
        self.assertEqual(runner.read_json(self.root / 'progressive/verified'/(record['path']+'.json'))['sha256'], record['sha256'])
        with mock.patch.object(self.module, 'stream_processes', side_effect=AssertionError('retransmitted verified file')):
            totals = self.module.copy_files(self.context, Path('/unused'), ['unused'], [record])
        self.assertEqual(totals['copied_bytes'], 0)
        self.assertEqual(totals['reused_bytes'], len(payload))
        target.write_bytes(b'corrupted')
        with self.assertRaisesRegex(self.module.OperationError, 'verified copy changed'):
            self.module.copy_files(self.context, Path('/unused'), ['unused'], [record])

    def test_final_copy_prioritizes_responses_and_resumes_bounded_checkpoint_chunks(self):
        self.spec['progressive_copy'] = {'poll_seconds': 1, 'bytes_per_second': 512 * 1024 * 1024,
                                         'timeout_seconds': 30}
        self.freeze()
        records = []
        for name, payload in (('checkpoints/adapter.bin', b'c' * (128 * 1024 * 1024 + 1024)),
                              ('responses/subject.json', b'saved subject response')):
            source = self.root / 'work/results' / name
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(payload)
            records.append({'path': str(source.relative_to(self.root)), 'bytes': len(payload),
                            'sha256': runner.sha256_file(source)})
        partial = self.root / 'progressive/partial' / records[0]['path']
        partial.parent.mkdir(parents=True)
        partial.write_bytes(b'c' * 100)
        requests = []
        def remote(_context, _key, _target, _operation, _flag, encoded):
            import shlex
            request = shlex.split(encoded)[0]
            requests.append(json.loads(request))
            return [sys.executable, '-B', str(self.operator), '--root', str(self.root),
                    '--config', str(self.config), '_remote-copy', '--files', request]
        with mock.patch.object(self.module, 'remote_arguments', side_effect=remote):
            totals = self.module.copy_files(self.context, Path('/unused'), ['unused'], records, terminal=True)
        self.assertEqual(requests[0][0]['path'], records[1]['path'])
        self.assertEqual(len(requests), 3)
        self.assertTrue(all(sum(r['length'] for r in group) <= 64 * 1024 * 1024 for group in requests))
        self.assertEqual(requests[0][1]['offset'], 100)
        self.assertEqual(totals['copied_files'], 2)
        self.assertEqual(totals['copied_bytes'], sum(r['bytes'] for r in records) - 100)
        for record in records:
            self.assertEqual(runner.sha256_file(self.root / 'result.next' / record['path']), record['sha256'])

    def test_progressive_copy_discovers_new_responses_between_checkpoint_chunks(self):
        self.spec['outputs'] = ['results']
        self.spec['progressive_copy'] = {'poll_seconds': 1, 'bytes_per_second': 512 * 1024 * 1024,
                                         'timeout_seconds': 30}
        self.freeze()
        checkpoint = self.root / 'work/results/checkpoints/adapter'
        checkpoint.mkdir(parents=True)
        (checkpoint / 'weights.bin').write_bytes(b'c' * (128 * 1024 * 1024 + 1024))
        runner.atomic_json(checkpoint / 'complete.json', {'weights.bin': runner.sha256_file(checkpoint / 'weights.bin')})
        runner.atomic_json(self.root / 'progressive/endpoint.json', {'identity': '/unused', 'target': ['unused']})
        weights = self.root / 'result.next/work/results/checkpoints/adapter/weights.bin'
        subject = self.root / 'result.next/work/results/responses/note/subjects.json'
        requests = []
        stream = self.module.stream_processes
        def remote(_context, _key, _target, _operation, _flag, encoded):
            import shlex
            request = shlex.split(encoded)[0]
            requests.append(json.loads(request))
            return [sys.executable, '-B', str(self.operator), '--root', str(self.root),
                    '--config', str(self.config), '_remote-copy', '--files', request]
        def copy(*args):
            stream(*args)
            if len(requests) == 1:
                self.assertFalse(weights.exists(), 'first transfer published the entire checkpoint')
                note = self.root / 'work/results/responses/note'
                note.mkdir(parents=True)
                (note / 'subjects.json').write_text('new response while checkpoint was copying')
                runner.atomic_json(note / 'complete.json', {'subjects.json': runner.sha256_file(note / 'subjects.json')})
            elif len(requests) == 2:
                self.assertTrue(subject.is_file(), 'new response waited behind the checkpoint')
                self.assertFalse(weights.exists())
            if weights.exists():
                runner.atomic_json(self.root / 'progressive/terminal.json', {'attempt_id': '001'})
        with mock.patch.object(self.module, 'remote_json', side_effect=lambda *args: self.call('_remote-progress')), \
                mock.patch.object(self.module, 'remote_arguments', side_effect=remote), \
                mock.patch.object(self.module, 'stream_processes', side_effect=copy), \
                mock.patch.object(self.module, 'stop', side_effect=AssertionError('copy stopped the worker')):
            result = self.module.progressive_copy(self.context, watch=True)
        self.assertEqual(result['state'], 'stopped')
        self.assertEqual(runner.sha256_file(weights), runner.sha256_file(checkpoint / 'weights.bin'))
        self.assertTrue(subject.is_file())
        self.assertEqual(len(requests), 3)

    def test_copy_rejects_invalid_chunk_length(self):
        self.freeze()
        for length in (-1, True, 4):
            with self.subTest(length=length), self.assertRaisesRegex(self.module.OperationError, 'length'):
                self.module.copy_records([{'path': 'work/results/response', 'bytes': 3,
                                          'sha256': '0' * 64, 'length': length}])

    def test_copy_publishes_completion_marker_after_its_directory_files(self):
        self.spec['outputs'] = ['results']
        self.spec['progressive_copy'] = {'poll_seconds': 1, 'bytes_per_second': 512 * 1024 * 1024,
                                         'timeout_seconds': 30}
        self.freeze()
        directory = self.root / 'work/results/checkpoints/adapter'
        directory.mkdir(parents=True)
        (directory / 'weights.bin').write_bytes(b'c' * (64 * 1024 * 1024 + 1024))
        runner.atomic_json(directory / 'complete.json', {'weights.bin': runner.sha256_file(directory / 'weights.bin')})
        records = self.call('_remote-progress')['files']
        def remote(_context, _key, _target, _operation, _flag, encoded):
            import shlex
            return [sys.executable, '-B', str(self.operator), '--root', str(self.root),
                    '--config', str(self.config), '_remote-copy', '--files', shlex.split(encoded)[0]]
        destination = self.root / 'result.next/work/results/checkpoints/adapter'
        with mock.patch.object(self.module, 'remote_arguments', side_effect=remote):
            self.module.copy_files(self.context, Path('/unused'), ['unused'], records, one_group=True)
            self.assertFalse((destination / 'complete.json').exists(), 'published completion before weights arrived')
            self.assertFalse((destination / 'weights.bin').exists())
            self.module.copy_files(self.context, Path('/unused'), ['unused'], records, terminal=True)
        self.assertEqual(runner.read_json(destination / 'complete.json'),
                         {'weights.bin': runner.sha256_file(destination / 'weights.bin')})

    def test_copy_stream_hash_failure_never_publishes_or_stops_worker(self):
        self.spec['progressive_copy'] = {'poll_seconds': 1, 'bytes_per_second': 65536, 'timeout_seconds': 30}
        self.freeze()
        record = {'path': 'work/results/subject.json', 'bytes': 3, 'sha256': '0' * 64}
        request = self.root / 'request.json'
        runner.atomic_json(request, [record])
        result = subprocess.run([sys.executable, '-B', str(self.operator), '--root', str(self.root), '--config', str(self.config),
            '_receive-copy', '--request', str(request)], input=b'bad', capture_output=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'hash mismatch', result.stderr)
        self.assertEqual((self.root / 'progressive/partial'/record['path']).read_bytes(), b'bad')
        self.assertFalse((self.root / 'result.next'/record['path']).exists())
        self.assertFalse((self.root / 'launch/stop-requested.json').exists())

    def test_copy_recovers_receipt_after_publication_without_rehashing_each_poll(self):
        self.spec['progressive_copy'] = {'poll_seconds': 1, 'bytes_per_second': 65536, 'timeout_seconds': 30}
        self.freeze()
        path = self.root / 'result.next/work/results/subject.json'
        path.parent.mkdir(parents=True)
        path.write_bytes(b'already published before the copier was interrupted')
        record = {'path': 'work/results/subject.json', 'bytes': path.stat().st_size, 'sha256': runner.sha256_file(path)}
        with mock.patch.object(self.module, 'sha256_file', wraps=self.module.sha256_file) as hashes:
            for _ in range(2):
                self.module.copy_files(self.context, Path('/unused'), ['unused'], [record])
            self.assertEqual(hashes.call_count, 1)

    def test_copier_start_failure_is_visible_and_does_not_stop_training(self):
        self.spec['progressive_copy'] = {'poll_seconds': 1, 'bytes_per_second': 65536, 'timeout_seconds': 30}
        self.freeze()
        with mock.patch.object(self.module, 'run', side_effect=[{'state': 'running', 'instance_id': '42'}, {'state': 'retrieved'}]), \
                mock.patch.object(self.module, 'resolve_ssh_target', return_value=['unused']), \
                mock.patch.object(self.module, 'start_progressive_copy', side_effect=OSError('copy connection failed')), \
                mock.patch.object(self.module.time, 'sleep'), mock.patch.object(self.module, 'stop') as stop:
            result = self.module.run_watch(self.context, None)
        self.assertEqual(result['state'], 'retrieved')
        self.assertEqual(result['progressive_copy']['state'], 'failed')
        self.assertIn('connection failed', result['progressive_copy']['error'])
        stop.assert_not_called()

    def test_copier_status_write_failure_does_not_stop_training(self):
        self.spec['progressive_copy'] = {'poll_seconds': 1, 'bytes_per_second': 65536, 'timeout_seconds': 30}
        self.freeze()
        publish = self.module.atomic_json
        def write(path, value, **kwargs):
            if path == self.root / 'progressive/status.json':
                raise OSError('local disk full')
            return publish(path, value, **kwargs)
        with mock.patch.object(self.module, 'run', side_effect=[{'state': 'running', 'instance_id': '42'}, {'state': 'retrieved'}]), \
                mock.patch.object(self.module, 'resolve_ssh_target', return_value=['unused']), \
                mock.patch.object(self.module, 'start_progressive_copy', side_effect=OSError('copy connection failed')), \
                mock.patch.object(self.module, 'atomic_json', side_effect=write), \
                mock.patch.object(self.module.time, 'sleep'), mock.patch.object(self.module, 'stop') as stop:
            self.assertEqual(self.module.run_watch(self.context, None)['state'], 'retrieved')
        stop.assert_not_called()

    def test_copier_exit_without_status_is_visible_and_does_not_stop_training(self):
        self.spec['progressive_copy'] = {'poll_seconds': 1, 'bytes_per_second': 65536, 'timeout_seconds': 30}
        self.freeze()
        copier = mock.Mock()
        copier.poll.return_value = 1
        copier.returncode = 1
        with mock.patch.object(self.module, 'run', side_effect=[{'state': 'running', 'instance_id': '42'}, {'state': 'retrieved'}]), \
                mock.patch.object(self.module, 'resolve_ssh_target', return_value=['unused']), \
                mock.patch.object(self.module, 'start_progressive_copy', return_value=copier), \
                mock.patch.object(self.module.time, 'sleep'), mock.patch.object(self.module, 'stop') as stop:
            result = self.module.run_watch(self.context, None)
        self.assertEqual(result['progressive_copy']['state'], 'failed')
        self.assertIn('exited with status 1', result['progressive_copy']['error'])
        stop.assert_not_called()

    def test_remote_copy_limits_bandwidth_and_refuses_symbolic_links(self):
        self.spec['progressive_copy'] = {'poll_seconds': 1, 'bytes_per_second': 65536, 'timeout_seconds': 30}
        self.freeze()
        path = self.root / 'work/results/payload'
        path.parent.mkdir(parents=True)
        path.write_bytes(b'x' * 65536)
        record = {'path': str(path.relative_to(self.root)), 'bytes': path.stat().st_size, 'sha256': runner.sha256_file(path)}
        command = [sys.executable, '-B', str(self.operator), '--root', str(self.root), '--config', str(self.config),
                   '_remote-copy', '--files', json.dumps([record])]
        started = time.monotonic()
        result = subprocess.run(command, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, path.read_bytes())
        self.assertGreaterEqual(time.monotonic()-started, 1.)
        path.unlink()
        path.symlink_to(self.input)
        result = subprocess.run(command, capture_output=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertRegex(result.stderr.decode(), 'symbolic link|escapes operation root')

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "operation"
        self.ledger = self.base / "budget-ledger.json"
        runner.atomic_json(self.ledger, {"lifetime_cap_cents": 100000, "actual_spend_cents": 0,
            "outstanding_commitments_cents": 0, "reserved_remaining_work_cents": 0, "entries": []})
        self.input = self.base / "input.txt"
        self.input.write_text("real workload input\n")
        self.offer = {"id": 123, "machine_id": 456, "bundle_id": 789, "num_gpus": 2,
            "gpu_name": "Tesla V100", "rentable": True, "rented": False, "is_bid": False,
            "verification": "verified", "disk_space": 100, "dph_total": .5,
            "inet_down_cost": .01, "inet_up_cost": .01}
        self.spec = {"version": 2, "label": "command-test", "offer": self.offer,
            "image": "docker.io/example/image@sha256:" + "a" * 64, "disk_gb": 100,
            "inputs": [{"source": str(self.input), "destination": "input.txt"}],
            "python": sys.executable,
            "command": [sys.executable, "-c", "from pathlib import Path; import os; "
                "Path('output.txt').write_text(Path('../package/input.txt').read_text() + os.environ['MARKER']); "
                "Path('invocations').open('a').write('once\\n')"],
            "environment": {"MARKER": "tested"}, "outputs": ["output.txt"],
            "limits": {"maximum_charge_cents": 1000, "maximum_hourly_usd": .562,
                "session_seconds": 7200, "work_seconds": 6000, "setup_cost_cents": 100,
                "manual_stop_cost_cents": 900, "inbound_gb": 20, "outbound_gb": 10}}

    def freeze(self):
        self.config = package.freeze(self.spec, self.root, self.ledger)
        self.operator = self.root / "transport/control/vast_full_build.py"
        definition = importlib.util.spec_from_file_location("frozen_command_operator", self.operator)
        self.module = importlib.util.module_from_spec(definition)
        self.enterContext(mock.patch.dict(sys.modules, {definition.name: self.module}))
        definition.loader.exec_module(self.module)
        self.context = self.module.Context.load(argparse.Namespace(root=self.root, config=self.config, operation="run"))

    def call(self, *arguments, returncode=0):
        result = subprocess.run([sys.executable, str(self.operator), "--root", str(self.root),
            "--config", str(self.config), *arguments], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, returncode, result.stderr)
        return json.loads(result.stdout) if returncode == 0 else result

    def transfer_receipts(self):
        for filename in ("approval-plan", "approval", "offer", "create-result", "instance", "pre-transfer-instance-validation"):
            runner.atomic_json(self.root / f"launch/{filename}.json", {})
        shutil.copyfile(self.ledger, self.root / "launch/reserved-budget-ledger.json")
        runner.atomic_json(self.root / "launch/full-build-reservation.json", {"ledger_sha256": runner.sha256_file(self.ledger)})
        self.assertTrue(self.call("_remote-verify-transfer")["verified"])

    def prepare_and_run(self):
        self.transfer_receipts()
        for _ in range(100):
            if self.call("_remote-prepare").get("prepared"):
                break
            time.sleep(.05)
        else:
            self.fail("real remote preparation did not finish")
        self.call("_remote-worker", "--attempt", "001")
        for _ in range(100):
            status = self.call("_remote-status", "--attempt", "001")
            if status["state"] == "terminal":
                break
            time.sleep(.05)
        else:
            self.fail("real worker did not finish")
        return status

    def test_real_command_preparation_execution_sealing_and_no_second_execution(self):
        self.freeze()
        self.assertEqual(self.prepare_and_run()["exit_status"], 0)
        self.assertEqual((self.root / "work/output.txt").read_text(), "real workload input\ntested")
        self.call("_remote-worker", "--attempt", "001")
        self.assertIn("consumed", self.call("_remote-worker", "--attempt", "002", returncode=1).stderr)
        self.assertEqual((self.root / "work/invocations").read_text(), "once\n")
        sealed = self.call("_remote-seal", "--attempt", "001")
        self.module.validate_file_records(self.root / "work", sealed["work_files"])
        (self.root / "work/output.txt").write_text("corruption")
        with self.assertRaisesRegex(self.module.OperationError, "integrity"):
            self.module.validate_file_records(self.root / "work", sealed["work_files"])

    def test_failing_workload_keeps_nonzero_terminal_evidence(self):
        self.spec["command"] = [sys.executable, "-c", "raise SystemExit(7)"]
        self.freeze()
        self.assertEqual(self.prepare_and_run()["exit_status"], 7)
        self.assertTrue(self.call("_remote-seal", "--attempt", "001")["terminal"])

    def test_changed_input_is_rejected_before_preparation(self):
        self.freeze()
        (self.root / "transport/workload/input.txt").write_text("changed")
        with self.assertRaisesRegex(self.module.OperationError, "verification failed"):
            self.module.verify_reviewed_artifacts(self.context)

    def test_real_ssh_configuration_ignores_inherited_files_and_keeps_options(self):
        self.freeze()
        private_key = self.root / "launch/ssh/id_ed25519"
        self.module.verify_local_ssh(self.context)
        self.assertFalse(private_key.parent.exists())
        private_key.parent.mkdir(parents=True)
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(private_key)],
                       check=True, capture_output=True, timeout=10)
        result = subprocess.run(
            self.module.ssh_arguments(self.context, private_key, ["-vv", "-G", "root@127.0.0.1"]),
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Reading configuration data", result.stderr.replace(
            "Reading configuration data /dev/null", ""))
        values = dict(line.split(" ", 1) for line in result.stdout.splitlines())
        expected = {"user": "root", "hostname": "127.0.0.1", "port": "22",
            "batchmode": "yes", "identitiesonly": "yes", "connecttimeout": "15",
            "connectionattempts": "2", "serveraliveinterval": "15", "serveralivecountmax": "3",
            "stricthostkeychecking": "accept-new", "identityfile": str(private_key),
            "userknownhostsfile": str(self.root / "launch/ssh/known_hosts")}
        for name, value in expected.items():
            self.assertEqual(values[name], value, name)
        self.assertEqual([line for line in result.stdout.splitlines() if line.startswith("identityfile ")],
                         [f"identityfile {private_key}"])

    def test_workload_launch_settings_are_frozen_and_forwarded_to_create(self):
        self.spec.update(onstart="ssh-keygen -A && service ssh start", ssh_direct=True)
        self.freeze()
        self.assertEqual(self.context.config["onstart"], self.spec["onstart"])
        self.assertIs(self.context.config["ssh_direct"], True)
        with mock.patch.dict(os.environ, {"VAST_API_KEY": "fake-api-key"}), \
                mock.patch.object(self.module.subprocess, "run") as create:
            self.module.invoke_private_create(self.context, self.offer, "fake-registry-token")
        args = create.call_args.args[0]
        self.assertEqual(args[args.index("--onstart-cmd") + 1], self.spec["onstart"])
        self.assertNotIn("fake-registry-token", args)
        self.assertEqual(create.call_args.kwargs["input"], b"fake-registry-token")

    def test_packager_rejects_invalid_launch_settings_before_writing(self):
        for field, value in (("onstart", None), ("onstart", ["command"]),
                             ("onstart", "bad\0script"), ("ssh_direct", "false"),
                             ("ssh_direct", 1)):
            with self.subTest(field=field, value=value):
                self.spec[field] = value
                root = self.base / f"invalid-{field}-{len(str(value))}"
                with self.assertRaisesRegex(runner.OperationError, field):
                    package.freeze(self.spec, root, self.ledger)
                self.assertFalse(root.exists())
                del self.spec[field]

    def test_direct_ssh_retries_real_authentication_with_current_port(self):
        self.spec["ssh_direct"] = True
        self.freeze()
        self.context.config["timing"].update(provider_attempts=2, provider_poll_seconds=0)
        directory = self.root / "launch/ssh"
        directory.mkdir(parents=True)
        (directory / "id_ed25519").write_text("fake private key")
        (directory / "id_ed25519.pub").write_text("ssh-ed25519 fake-public-key")
        instances = [{"id": 42, "public_ipaddr": "198.51.100.42",
                      "ports": {"22/tcp": [{"HostIp": "0.0.0.0", "HostPort": port},
                                           {"HostIp": "::", "HostPort": port}]}}
                     for port in ("35960", "36002")]
        authenticated = []

        def process(args, **kwargs):
            if args[:3] == ["vastai", "attach", "ssh"]:
                return subprocess.CompletedProcess(args, 0, b"attached", b"")
            self.assertEqual(args[0], "ssh", "direct mode must not ask ssh-url for a proxy")
            self.assertEqual(args[-1], "true")
            self.assertTrue((self.root / "launch/ssh-attach-delivered.json").exists())
            self.assertFalse((self.root / "launch/ssh-attached.json").exists())
            authenticated.append(args)
            if len(authenticated) == 1:
                raise self.module.OperationError("public key not usable yet")
            return subprocess.CompletedProcess(args, 0, b"", b"")

        with mock.patch.object(self.module, "vast_json", side_effect=instances) as provider, \
                mock.patch.object(self.module, "completed_process", side_effect=process) as commands:
            _, target = self.module.ensure_ssh(self.context, "42")
        self.assertEqual(target, ["-p", "36002", "root@198.51.100.42"])
        self.assertEqual([args[args.index("-p") + 1] for args in authenticated], ["35960", "36002"])
        self.assertEqual(provider.call_args_list, [mock.call(["show", "instance", "42", "--raw"])] * 2)
        self.assertEqual(sum(c.args[0][:3] == ["vastai", "attach", "ssh"] for c in commands.call_args_list), 1)
        self.assertTrue((self.root / "launch/ssh-attached.json").exists())

    def test_direct_endpoint_refuses_missing_invalid_or_wrong_instance_without_proxy(self):
        self.spec["ssh_direct"] = True
        self.freeze()
        good = {"id": 42, "public_ipaddr": "198.51.100.42",
                "ports": {"22/tcp": [{"HostPort": "35960"}]}}
        bad = [{**good, "id": 43}, {**good, "public_ipaddr": "host;command"},
               {**good, "public_ipaddr": "0.0.0.0"}, {**good, "ports": None},
               {**good, "ports": {"22/tcp": []}}]
        bad += [{**good, "ports": {"22/tcp": [{"HostPort": p}]}}
                for p in (None, True, 0, 65536, "22 -oProxyCommand=bad")]
        bad.append({**good, "ports": {"22/tcp": [{"HostPort": "22"}, {"HostPort": "23"}]}})
        with mock.patch.object(self.module, "completed_process", side_effect=AssertionError("no proxy fallback")):
            for instance in bad:
                with self.subTest(instance=instance), self.assertRaises(self.module.OperationError):
                    self.module.resolve_ssh_target(self.context, "42", instance)
            ipv6 = {**good, "public_ipaddr": "2001:db8::42",
                    "ports": {"22/tcp": [{"HostIp": "0.0.0.0", "HostPort": "22"},
                                         {"HostIp": "::", "HostPort": "35960"}]}}
            self.assertEqual(self.module.resolve_ssh_target(self.context, "42", ipv6),
                             ["-p", "35960", "root@2001:db8::42"])

    def test_actual_100gb_two_gpu_instance_admitted_by_original_readiness_loop(self):
        self.freeze()
        instance = {**self.offer, "id": 42, "label": self.spec["label"], "image_uuid": self.spec["image"],
                    "actual_status": "running", "intended_status": "running"}
        with mock.patch.object(self.module, "vast_json", return_value=instance):
            result = self.module.freeze_running_instance(self.context, self.offer, {"new_contract": 42, "success": True})
        self.assertEqual(result["num_gpus"], 2)
        self.assertEqual(result["disk_space"], 100)

    def test_readiness_accepts_distinct_bundle_ids_and_records_both(self):
        self.freeze()
        self.context.config["timing"].update(provider_attempts=2, provider_poll_seconds=0)
        instance = {**self.offer, "id": 42, "bundle_id": 987, "label": self.spec["label"],
                    "image_uuid": self.spec["image"], "actual_status": "running", "intended_status": "running"}
        with mock.patch.object(self.module, "vast_json", return_value=instance) as provider:
            actual = self.module.freeze_running_instance(self.context, self.offer, {"new_contract": 42, "success": True})
        self.assertEqual(actual["bundle_id"], 987)
        self.assertEqual(provider.call_count, 1)
        receipt = runner.read_json(self.root / "launch/pre-transfer-instance-validation.json")
        self.assertEqual(receipt["offer_bundle_id"], "789")
        self.assertEqual(receipt["bundle_id"], "987")

    def test_running_hardware_mismatch_reports_field_without_retry(self):
        self.freeze()
        self.context.config["timing"].update(provider_attempts=3, provider_poll_seconds=0)
        instance = {**self.offer, "id": 42, "num_gpus": 1, "label": self.spec["label"],
                    "image_uuid": self.spec["image"], "actual_status": "running", "intended_status": "running"}
        with mock.patch.object(self.module, "vast_json", return_value=instance) as provider:
            with self.assertRaisesRegex(self.module.OperationError, "num_gpus"):
                self.module.freeze_running_instance(self.context, self.offer, {"new_contract": 42, "success": True})
        self.assertEqual(provider.call_count, 1)
        self.assertFalse((self.root / "launch/pre-transfer-instance-validation.json").exists())

    def test_stop_destroys_created_instance_even_when_hardware_is_rejected(self):
        self.freeze()
        self.context.config["timing"].update(destroy_attempts=2, destroy_poll_seconds=0)
        runner.atomic_json(self.root / "launch/create-result.json", {"success": True, "new_contract": 42})
        runner.atomic_json(self.root / "launch/offer.json", [self.offer])
        instance = {**self.offer, "id": 42, "num_gpus": 1, "label": self.spec["label"],
                    "image_uuid": self.spec["image"]}
        # Provider inventory/destruction and deferred billing are the only fakes.
        # stop, ownership checks, destroy requests and absence verification are real.
        with mock.patch.object(self.module, "sanitized_live_instances", side_effect=[[instance], [], []]), \
                mock.patch.object(self.module, "completed_process", return_value=subprocess.CompletedProcess([], 0, b"", b"")) as command, \
                mock.patch.object(self.module, "ensure_final_charge", return_value=None), \
                mock.patch.object(self.module, "invoice_pending_result", return_value={"state": "invoice_pending"}):
            self.assertEqual(self.module.stop(self.context)["state"], "invoice_pending")
        self.assertEqual(command.call_count, 1)
        self.assertEqual(command.call_args.args[0][:4], ["vastai", "destroy", "instance", "42"])
        proof = runner.read_json(self.root / "launch/destruction-confirmation.json")
        self.assertEqual(proof["absence_observations"], 2)

    def test_readiness_retries_provider_failure_and_waits_for_running(self):
        self.freeze()
        self.context.config["timing"].update(provider_attempts=4, provider_poll_seconds=0)
        instance = {**self.offer, "id": 42, "label": self.spec["label"], "image_uuid": self.spec["image"],
                    "actual_status": "running", "intended_status": "running"}
        with mock.patch.object(self.module, "vast_json", side_effect=[
                self.module.OperationError("temporary provider failure"),
                {**instance, "actual_status": "loading"}, {**instance, "actual_status": "created"}, instance]) as provider:
            actual = self.module.freeze_running_instance(self.context, self.offer, {"new_contract": 42, "success": True})
        self.assertEqual(actual["actual_status"], "running")
        self.assertEqual(provider.call_count, 4)

    def test_cleanup_refuses_other_instance_or_conflicting_label(self):
        self.freeze()
        runner.atomic_json(self.root / "launch/create-result.json", {"success": True, "new_contract": 42})
        runner.atomic_json(self.root / "launch/offer.json", [self.offer])
        for identifier, label in ((99, self.spec["label"]), (42, "other-operation")):
            with self.subTest(identifier=identifier, label=label):
                with self.assertRaises(self.module.OperationError):
                    self.module.verify_destroy_ownership(self.context, "42", {"id": identifier, "label": label})

    def test_admission_still_rejects_changed_approved_terms(self):
        self.freeze()
        instance = {**self.offer, "id": 42, "label": self.spec["label"], "image_uuid": self.spec["image"],
                    "actual_status": "running", "intended_status": "running"}
        for field, value in (("machine_id", 999), ("gpu_name", "Other GPU"), ("num_gpus", 1),
                             ("disk_space", 99), ("dph_total", .6), ("is_bid", True),
                             ("verification", "unverified"), ("label", "other-operation"),
                             ("image_uuid", "example/wrong@sha256:" + "b" * 64)):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, field):
                    self.module.validate_instance_against_offer(self.offer, {"success": True, "new_contract": 42},
                        {**instance, field: value}, self.spec["image"], 562000,
                        expected_label=self.spec["label"], minimum_disk_gb=100)

    def test_missing_instance_waits_but_wrong_instance_id_does_not(self):
        self.freeze()
        self.context.config["timing"].update(provider_attempts=3, provider_poll_seconds=0)
        instance = {**self.offer, "id": 99, "label": self.spec["label"], "image_uuid": self.spec["image"],
                    "actual_status": "running", "intended_status": "running"}
        with mock.patch.object(self.module, "vast_json", side_effect=[{"instances": None}, instance]) as provider:
            with self.assertRaisesRegex(self.module.OperationError, "instance.*(match|ID)"):
                self.module.freeze_running_instance(self.context, self.offer, {"new_contract": 42, "success": True})
        self.assertEqual(provider.call_count, 2)

    def test_selected_offer_is_an_input_not_a_search_to_repeat(self):
        self.freeze()
        query, offer = self.module.select_offer(self.context)
        with mock.patch.object(self.module, "search_offers", side_effect=AssertionError("must not repeat offer selection")):
            self.assertEqual(self.module.refresh_approved_offer(self.context, {"offer": offer, "offer_query": query}), offer)

    def test_package_rejects_unrecognized_old_spec_and_overlapping_inputs(self):
        self.spec["version"] = 1
        with self.assertRaisesRegex(runner.OperationError, "version-2"):
            package.freeze(self.spec, self.root, self.ledger)
        self.spec["version"] = 2
        self.spec["inputs"].append(self.spec["inputs"][0])
        with self.assertRaisesRegex(runner.OperationError, "overlap"):
            package.freeze(self.spec, self.root, self.ledger)
        self.assertFalse(self.root.exists())

    def test_cost_estimate_preserves_unknown_charges_and_rounds_up(self):
        self.spec["limits"].update(inbound_gb=1, outbound_gb=0)
        self.offer["inet_down_cost"] = 0.000000001
        self.freeze()
        self.assertEqual(self.context.limits["transfer_allowance_micro_usd"], 1)
        base = {"id": 42, "duration": 0.000001, "dph_total": .5}
        for fields in ({}, {"inet_down_billed": None, "inet_up_billed": None},
                       {"inet_down_billed": 0, "inet_up_billed": 0},
                       {"inet_down_billed": "unverified", "inet_up_billed": 999999999999}):
            with self.subTest(fields=fields):
                cost = self.module.cost_record_from_instance(self.context, "42", {**base, **fields})
                self.assertEqual(cost["estimated_rental_micro_usd"], 1)
                self.assertEqual(cost["estimated_total_micro_usd"], 2)
                self.assertIsNone(cost["provider_reported_total_micro_usd"])

    def test_cost_estimate_rejects_invalid_duration_rate_and_identity(self):
        self.freeze()
        base = {"id": 42, "duration": 60, "dph_total": .5}
        for field in ("duration", "dph_total"):
            for value in (None, True, -1, float("nan"), float("inf"), "invalid"):
                with self.subTest(field=field, value=value):
                    with self.assertRaisesRegex(self.module.OperationError, field):
                        self.module.cost_record_from_instance(self.context, "42", {**base, field: value})
        for rate in (0, .562001):
            with self.assertRaisesRegex(self.module.OperationError, "dph_total"):
                self.module.cost_record_from_instance(self.context, "42", {**base, "dph_total": rate})
        with self.assertRaisesRegex(self.module.OperationError, "instance ID"):
            self.module.cost_record_from_instance(self.context, "43", base)

    def test_contract_refuses_missing_or_invalid_transfer_allowance(self):
        self.freeze()
        self.context.limits.pop("transfer_allowance_micro_usd")
        with self.assertRaisesRegex(self.module.OperationError, "transfer_allowance"):
            self.context.validate()
        for value in (None, True, -1, 10_000_001):
            self.context.limits["transfer_allowance_micro_usd"] = value
            with self.assertRaisesRegex(self.module.OperationError, "transfer.allowance"):
                self.context.validate()
        self.context.limits["transfer_allowance_micro_usd"] = 0
        self.context.validate()  # Explicitly approved zero is different from missing.

    def test_packaging_refuses_unknown_transfer_prices_and_excess_budget(self):
        for field in ("inet_down_cost", "inet_up_cost"):
            price = self.offer.pop(field)
            with self.assertRaisesRegex(ValueError, field):
                package.freeze(self.spec, self.root, self.ledger)
            self.assertFalse(self.root.exists())
            self.offer[field] = price
        self.spec["limits"]["inbound_gb"] = 1000
        with self.assertRaisesRegex(runner.OperationError, "exceed.*maximum charge"):
            package.freeze(self.spec, self.root, self.ledger)
        self.assertFalse(self.root.exists())

    def lifecycle_fixture(self):
        import test_vast_full_build as original
        fixture = original.VastFullBuildCliTest()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        # Retain the successful controller's provider fixture; account only for
        # the now-configurable private-create disk argument, not a new fake lifecycle.
        command = FAKE_COMMAND.replace(
            'marker = Path(args[-2])\n        outcome = Path(args[-1])',
            'offset = next(i for i, a in enumerate(args) if a.endswith("vast_private_create.py"))\n'
            '        marker = Path(args[offset + 4])\n        outcome = Path(args[offset + 5])')
        command = command.replace('"ssh_host": "fake.example",',
            '"public_ipaddr": "198.51.100.42", "ports": {"22/tcp": [{"HostPort": "35960"}]},\n'
            '        "ssh_host": "fake.example",')
        for name in ("docker", "tar", "vastai", "uvx", "ssh", "ssh-keygen", "nvidia-smi"):
            (fixture.bin / name).write_text(command)
        offer_result = subprocess.run([str(fixture.bin / "vastai"), "search", "offers"],
            env=fixture.environment, capture_output=True, text=True, check=True)
        self.spec.update(offer=json.loads(offer_result.stdout)[0], label="crec-test-gte-full-build",
                         image="docker.io/kernelkind/oracle-mvp@sha256:" + "9" * 64, disk_gb=200,
                         outputs=["result.bin"])
        self.spec["limits"]["maximum_hourly_usd"] = 1.36
        self.freeze()
        configuration = runner.read_json(self.config)
        configuration["timing"] = fixture.operation_contract()["timing"]
        runner.atomic_json(self.config, configuration, replace=True)
        fixture.root, fixture.operator, fixture.config, fixture.ledger = self.root, self.operator, self.config, self.ledger
        fixture.environment["FAKE_FULL_BUILD_ROOT"] = str(self.root)
        prepared = fixture.prepare()
        missing = fixture.invoke("run", "--approve", prepared["approval_sha256"])
        self.assertNotEqual(missing.returncode, 0)
        self.assertEqual(fixture.provider()["create_calls"], 0)
        ledger = runner.read_json(self.ledger)
        ledger["outstanding_commitments_cents"] = 1000
        ledger["entries"] = [{**prepared["reservation"], "reservation_id": "fixture", "status": "reserved"}]
        runner.atomic_json(self.ledger, ledger, replace=True)
        message = self.base / "commit-message"
        message.write_text("Reserve simulated command workload\n")
        for args in (["init", "--quiet"], ["add", self.ledger.name],
                     ["-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--quiet", "-F", str(message)]):
            subprocess.run(["git", "-C", str(self.base), *args], check=True, capture_output=True)
        return fixture

    def test_command_prepare_and_run_reject_local_ssh_failure_without_spending(self):
        fixture = self.lifecycle_fixture()
        fixture.set_provider(fail_ssh_config=True)
        ledger_before = self.ledger.read_bytes()
        for operation in ("prepare", "run"):
            with self.subTest(operation=operation):
                result = fixture.invoke(operation)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("local SSH configuration", result.stderr)
                self.assertEqual(self.ledger.read_bytes(), ledger_before)
                self.assertEqual(fixture.provider()["create_calls"], 0)
                self.assertFalse((self.root / "launch/full-build-reservation.json").exists())
                self.assertFalse((self.root / "launch/create-request-attempted.txt").exists())

    def test_completed_command_is_retrieved_without_automatic_deletion(self):
        fixture = self.lifecycle_fixture()
        started = fixture.invoke_with_tty_secret("run")
        self.assertEqual(started.returncode, 0, started.stderr)
        fixture.set_provider(remote_status="terminal")
        completed = fixture.invoke("run")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue((self.root / "launch/retrieval-verification.json").exists())
        self.assertEqual(fixture.provider()["destroy_calls"], 0)
        self.assertEqual(len(fixture.provider()["instances"]), 1)
        self.assertTrue(fixture.output_json(completed)["billing_possible"])
        self.assertTrue(fixture.output_json(completed)["manual_stop_recommended"])

    def test_watch_manifest_error_stops_and_retrieves_without_deleting(self):
        fixture = self.lifecycle_fixture()
        self.assertEqual(fixture.invoke_with_tty_secret("run").returncode, 0)
        context = self.module.Context.load(argparse.Namespace(
            root=self.root, config=self.config, operation="run"))

        def add_cache(_seconds):
            path = self.root / "transport/control/__pycache__/monitoring.pyc"
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b"unexpected monitoring cache")

        # Real run/watch/stop, manifest checks, retrieval and CLI provider boundary.
        # Add the same kind of unexpected file between watcher iterations.
        with mock.patch.dict(os.environ, fixture.environment), \
                mock.patch.object(self.module.time, "sleep", side_effect=add_cache):
            with self.assertRaisesRegex(self.module.OperationError, "file set"):
                self.module.run_watch(context, None)
        self.assertEqual(fixture.provider()["remote_status"], "terminal")
        self.assertTrue((self.root / "launch/retrieval-verification.json").exists())
        self.assertEqual(fixture.provider()["destroy_calls"], 0)
        self.assertEqual(len(fixture.provider()["instances"]), 1)
        self.assertFalse((self.root / "launch/result-loss-ledger-reconciliation.json").exists())
        self.assertEqual(fixture.invoke("stop").returncode, 0)
        self.assertEqual(fixture.provider()["destroy_calls"], 1)

    def test_watch_deadline_preserves_instance_even_without_ssh(self):
        fixture = self.lifecycle_fixture()
        self.assertEqual(fixture.invoke_with_tty_secret("run").returncode, 0)
        runner.atomic_json(self.root / "launch/watch-deadline.json",
                           {"deadline_utc": "2000-01-01T00:00:00Z"})
        fixture.set_provider(fail_all_ssh=True, allow_destroy_without_retrieval=True)
        expired = fixture.invoke("run", "--watch")
        self.assertEqual(expired.returncode, 0, expired.stderr)
        self.assertTrue(fixture.output_json(expired)["instance_preserved"])
        self.assertIn("retrieval_error", fixture.output_json(expired))
        self.assertEqual(fixture.output_json(expired)["state"], "manual_stop_required")
        self.assertEqual(fixture.provider()["remote_status"], "running")
        self.assertEqual(fixture.provider()["destroy_calls"], 0)
        self.assertEqual(len(fixture.provider()["instances"]), 1)
        self.assertFalse((self.root / "launch/result-loss-ledger-reconciliation.json").exists())
        self.assertEqual(fixture.invoke("stop").returncode, 0)
        self.assertEqual(fixture.provider()["destroy_calls"], 1)

    def test_failed_command_retains_instance_and_partial_results(self):
        fixture = self.lifecycle_fixture()
        self.assertEqual(fixture.invoke_with_tty_secret("run").returncode, 0)
        fixture.set_provider(remote_status="terminal", remote_terminal_kind="start.exit")
        failed = fixture.invoke("run", "--watch")
        self.assertEqual(failed.returncode, 0, failed.stderr)
        self.assertTrue(fixture.output_json(failed)["instance_preserved"])
        self.assertTrue((self.root / "result.next/work/full-build-attempts/001/start.exit").exists())
        self.assertEqual(fixture.provider()["destroy_calls"], 0)
        self.assertEqual(fixture.invoke("run").returncode, 0)
        self.assertEqual(fixture.provider()["destroy_calls"], 0)

    def test_command_lifecycle_uses_original_recovery_transfer_and_destroy(self):
        self.spec.update(onstart="ssh-keygen -A && service ssh start", ssh_direct=True)
        fixture = self.lifecycle_fixture()
        fixture.set_provider(lose_worker_ack_once=True)
        first = fixture.invoke_with_tty_secret("run")
        self.assertNotEqual(first.returncode, 0)
        resumed = fixture.invoke("run")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(fixture.output_json(resumed)["state"], "running")
        self.assertEqual(fixture.provider()["create_calls"], 1)
        self.assertEqual(fixture.provider()["worker_start_calls"], 1)
        # Status and resumed execution must resolve the current mapping, not
        # the original port or the proxy returned by ssh-url.
        fixture.set_instance(ports={"22/tcp": [{"HostPort": "36002"}]})
        status = fixture.invoke("status")
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(fixture.output_json(status)["state"], "running")
        fixture.set_provider(remote_status="terminal")
        completed = fixture.invoke("run")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(fixture.output_json(completed)["state"], "retrieved")
        self.assertTrue((self.root / "result/audit/local-verification.json").exists())
        self.assertEqual(fixture.provider()["destroy_calls"], 0)
        self.assertEqual(len(fixture.provider()["instances"]), 1)
        self.assertEqual(runner.read_json(self.ledger)["outstanding_commitments_cents"], 1000)
        self.assertEqual(fixture.invoke("run").returncode, 0)
        self.assertEqual(fixture.provider()["create_calls"], 1)
        self.assertEqual(fixture.provider()["destroy_calls"], 0)
        stopped = fixture.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(fixture.output_json(stopped)["state"], "ledger_reconciliation_required")
        self.assertEqual(fixture.provider()["destroy_calls"], 1)
        self.assertEqual(fixture.provider()["instances"], [])

        calls = fixture.calls()
        self.assertFalse(any(c["tool"] == "vastai" and c["argv"][:1] == ["ssh-url"] for c in calls))
        create = next(c["argv"] for c in calls if c["tool"] == "uvx")
        self.assertEqual(create[create.index("--onstart-cmd") + 1], self.spec["onstart"])
        ssh = [c["argv"] for c in calls if c["tool"] == "ssh" and "-G" not in c["argv"]]
        self.assertTrue(all("root@198.51.100.42" in args for args in ssh))
        self.assertEqual(ssh[-1][ssh[-1].index("-p") + 1], "36002")

    def test_cli_distinct_bundles_reach_worker_and_stop_deletes_once(self):
        fixture = self.lifecycle_fixture()
        fixture.set_provider(crash_on_first_show_instance=True)
        interrupted = fixture.invoke_with_tty_secret("run")
        self.assertNotEqual(interrupted.returncode, 0)
        fixture.set_instance(bundle_id=418499128)
        started = fixture.invoke("run")
        self.assertEqual(started.returncode, 0, started.stderr)
        self.assertEqual(fixture.output_json(started)["state"], "running")
        receipt = runner.read_json(self.root / "launch/pre-transfer-instance-validation.json")
        self.assertEqual(receipt["bundle_id"], "418499128")
        self.assertEqual(receipt["offer_bundle_id"], str(self.spec["offer"]["bundle_id"]))
        stopped = fixture.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(fixture.provider()["create_calls"], 1)
        self.assertEqual(fixture.provider()["worker_start_calls"], 1)
        self.assertEqual(fixture.provider()["destroy_calls"], 1)
        self.assertEqual(fixture.provider()["instances"], [])

    def test_cli_null_transfer_billing_uses_estimate_and_reconciles_actual_charge(self):
        fixture = self.lifecycle_fixture()
        fixture.set_provider(crash_on_first_show_instance=True)
        interrupted = fixture.invoke_with_tty_secret("run")
        self.assertNotEqual(interrupted.returncode, 0)
        fixture.set_instance(duration=60, inet_down_billed=None, inet_up_billed=None,
                             inet_down_cost=None, inet_up_cost=None)
        started = fixture.invoke("run")
        self.assertEqual(started.returncode, 0, started.stderr)
        self.assertEqual(fixture.output_json(started)["state"], "running")
        self.assertEqual(fixture.provider()["worker_start_calls"], 1)
        cost = fixture.output_json(fixture.invoke("status"))["cost"]
        # 30 GB at the saved offer's $0.0078125/GB, plus one minute at
        # the approved maximum $1.36/hour. None of these are posted charges.
        self.assertEqual(cost["transfer_allowance_micro_usd"], 234375)
        self.assertEqual(cost["estimated_rental_micro_usd"], 22667)
        self.assertEqual(cost["estimated_total_micro_usd"], 257042)
        self.assertIsNone(cost["provider_reported_total_micro_usd"])
        self.assertNotIn("conservative_observed_total_micro_usd", cost)
        # Missing counters are also unknown, not an observed zero charge.
        instances = fixture.provider()["instances"]
        for key in ("inet_down_billed", "inet_up_billed", "inet_down_cost", "inet_up_cost"):
            instances[0].pop(key)
        fixture.set_provider(instances=instances)
        absent_cost = fixture.output_json(fixture.invoke("status"))["cost"]
        self.assertEqual(absent_cost["estimated_total_micro_usd"], cost["estimated_total_micro_usd"])
        self.assertIsNone(absent_cost["provider_reported_total_micro_usd"])
        fixture.set_instance(duration=25000)
        warning = fixture.output_json(fixture.invoke("status"))
        self.assertTrue(warning["manual_stop_recommended"])
        self.assertIsNone(warning["cost"]["provider_reported_total_micro_usd"])
        stopped = fixture.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(fixture.provider()["destroy_calls"], 1)
        actual = runner.read_json(self.root / "launch/provider-final-charge.json")
        self.assertEqual(actual["actual_charge_micro_usd"], 1250000)
        # The estimate must neither settle the ledger nor release its reserve.
        self.assertEqual(runner.read_json(self.ledger)["actual_spend_cents"], 0)
        self.assertEqual(runner.read_json(self.ledger)["outstanding_commitments_cents"], 1000)

    def test_cli_setup_gate_includes_full_transfer_allowance_when_billing_unknown(self):
        fixture = self.lifecycle_fixture()
        fixture.set_provider(crash_on_first_show_instance=True)
        self.assertNotEqual(fixture.invoke_with_tty_secret("run").returncode, 0)
        fixture.set_instance(duration=2500, inet_down_billed=None, inet_up_billed=None)
        refused = fixture.invoke("run")
        self.assertEqual(refused.returncode, 0, refused.stderr)
        self.assertIn("setup cost estimate", (self.root / "launch/preworker-instance-failure.log").read_text())
        receipt = runner.read_json(next((self.root / "launch/pre-worker-cost-observations").glob("*.json")))
        self.assertLess(receipt["estimated_rental_micro_usd"], 1_000_000)
        self.assertGreater(receipt["estimated_total_micro_usd"], 1_000_000)
        self.assertEqual(fixture.provider()["worker_start_calls"], 0)
        self.assertEqual(fixture.provider()["destroy_calls"], 0)
        self.assertTrue(fixture.output_json(refused)["instance_preserved"])

    def test_cli_changed_transfer_allowance_invalidates_approval_before_create(self):
        fixture = self.lifecycle_fixture()
        configuration = runner.read_json(self.config)
        configuration["limits"]["transfer_allowance_micro_usd"] = 0
        runner.atomic_json(self.config, configuration, replace=True)
        rejected = fixture.invoke_with_tty_secret("run")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertEqual(fixture.provider()["create_calls"], 0)

    def test_cli_changed_startup_or_endpoint_invalidates_approval_before_create(self):
        fixture = self.lifecycle_fixture()
        original = runner.read_json(self.config)
        for field, value in (("onstart", "ssh-keygen -A && service ssh start"), ("ssh_direct", True)):
            with self.subTest(field=field):
                configuration = {**original, field: value}
                runner.atomic_json(self.config, configuration, replace=True)
                rejected = fixture.invoke_with_tty_secret("run")
                self.assertNotEqual(rejected.returncode, 0)
                self.assertEqual(fixture.provider()["create_calls"], 0)

    def test_direct_port_disappearing_does_not_prevent_stop_and_verified_deletion(self):
        self.spec["ssh_direct"] = True
        fixture = self.lifecycle_fixture()
        started = fixture.invoke_with_tty_secret("run")
        self.assertEqual(started.returncode, 0, started.stderr)
        self.assertEqual(fixture.provider()["worker_start_calls"], 1)
        fixture.set_instance(ports=None)
        fixture.set_provider(allow_destroy_without_retrieval=True)
        stopped = fixture.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(fixture.provider()["destroy_calls"], 1)
        self.assertEqual(fixture.provider()["instances"], [])
        self.assertTrue((self.root / "launch/destruction-confirmation.json").exists())
        self.assertEqual(runner.read_json(self.ledger)["outstanding_commitments_cents"], 1000)
        self.assertFalse(any(c["tool"] == "vastai" and c["argv"][:1] == ["ssh-url"]
                             for c in fixture.calls()))

    def test_cli_hardware_rejection_preserves_instance_without_uploading_or_starting(self):
        fixture = self.lifecycle_fixture()
        fixture.set_provider(crash_on_first_show_instance=True)
        interrupted = fixture.invoke_with_tty_secret("run")
        self.assertNotEqual(interrupted.returncode, 0)
        fixture.set_instance(num_gpus=99, bundle_id=418499128)
        previous_queries = fixture.provider()["show_instance_calls"]
        rejected = fixture.invoke("run")
        self.assertEqual(rejected.returncode, 0, rejected.stderr)
        self.assertIn("num_gpus", (self.root / "launch/preworker-instance-failure.log").read_text())
        self.assertEqual(fixture.provider()["show_instance_calls"], previous_queries + 1)
        self.assertEqual(fixture.provider()["remote_prepare_calls"], 0)
        self.assertEqual(fixture.provider()["worker_start_calls"], 0)
        self.assertEqual(fixture.provider()["destroy_calls"], 0)
        self.assertEqual(len(fixture.provider()["instances"]), 1)
        self.assertEqual(fixture.invoke("stop").returncode, 0)
        self.assertEqual(fixture.provider()["destroy_calls"], 1)

    def test_watch_resumes_shared_run_until_retrieval_without_second_approval(self):
        self.freeze()
        states = [{'state': 'preparing'}, {'state': 'running'}, {'state': 'retrieved'}]
        with mock.patch.object(self.module, 'run', side_effect=states) as run, mock.patch.object(runner.time, 'sleep'):
            self.assertEqual(self.module.run_watch(self.context, 'approved'), states[-1])
        self.assertEqual(run.call_args_list, [mock.call(self.context, 'approved'),
            mock.call(self.context, None), mock.call(self.context, None)])

    def test_watch_keeps_original_deadline_and_preserves_instance_on_expiry(self):
        self.freeze()
        runner.atomic_json(self.root / 'launch/watch-deadline.json', {'deadline_utc': '2000-01-01T00:00:00Z'})
        runner.atomic_bytes(self.root / 'launch/create-request-attempted.txt', b'attempted')
        with mock.patch.object(self.module, 'run') as run, mock.patch.object(self.module, 'stop', return_value={'state': 'retrieved', 'instance_preserved': True}) as stop:
            self.assertEqual(self.module.run_watch(self.context, None)['state'], 'retrieved')
        run.assert_not_called()
        stop.assert_called_once_with(self.context, delete=False)

    def test_watch_reserves_cleanup_time_and_preserves_instance_after_controller_error(self):
        self.spec['limits']['cleanup_seconds'] = 600
        self.freeze()
        self.assertEqual(self.context.config['cleanup_seconds'], 600)
        runner.atomic_bytes(self.root / 'launch/create-request-attempted.txt', b'attempted')
        now = self.module.utc_now()
        with mock.patch.object(self.module, 'utc_now', return_value=now), \
                mock.patch.object(self.module, 'run', side_effect=ValueError('bad provider response')), \
                mock.patch.object(self.module, 'stop') as stop:
            with self.assertRaisesRegex(ValueError, 'bad provider response'):
                self.module.run_watch(self.context, None)
        deadline = runner.read_json(self.root / 'launch/watch-deadline.json')['deadline_utc']
        remaining = (self.module.parse_utc(deadline, 'deadline') - now).total_seconds()
        self.assertAlmostEqual(remaining, 6600, delta=1)
        stop.assert_called_once_with(self.context, delete=False)


    def test_interrupt_during_watch_poll_stops_work_without_deleting(self):
        self.freeze()
        runner.atomic_bytes(self.root / 'launch/create-request-attempted.txt', b'attempted')
        with mock.patch.object(self.module, 'run', return_value={'state': 'running'}), \
                mock.patch.object(self.module.time, 'sleep', side_effect=KeyboardInterrupt), \
                mock.patch.object(self.module, 'stop') as stop:
            with self.assertRaises(KeyboardInterrupt):
                self.module.run_watch(self.context, None)
        stop.assert_called_once_with(self.context, delete=False)

    def test_second_watch_cannot_interrupt_the_active_operator(self):
        self.freeze()
        with self.module.file_lock(self.root / 'watch.lock', blocking=False), \
                mock.patch.object(self.module, 'run', return_value={'state': 'invoice_pending'}) as run, \
                mock.patch.object(self.module, 'stop') as stop:
            with self.assertRaisesRegex(self.module.OperationError, "lock is held"):
                self.module.run_watch(self.context, None)
        run.assert_not_called()
        stop.assert_not_called()



if __name__ == "__main__":
    unittest.main()
